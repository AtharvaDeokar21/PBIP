import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_customer
from app.models.ai import AIConversation, AIMessage
from app.models.banking import Account, Transaction
from app.models.identity import Customer
from app.models.products import CustomerInvestment, LoanProduct
from app.schemas.ai import AIChatRequest, AIChatResponse, ConversationResponse, MessageResponse
from app.services import (
    account_service,
    customer_service,
    loan_service,
    recommendation_service,
)
from app.services.common import to_money, utcnow

router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"],
)


@router.post("/chat", response_model=AIChatResponse)
async def chat(
    payload: AIChatRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> AIChatResponse:
    now = utcnow()
    user_msg_text = payload.message.strip()
    if not user_msg_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty")

    # 1. Resolve or create conversation
    conv_id = payload.conversation_id
    conversation: AIConversation | None = None
    if conv_id:
        conversation = await db.get(AIConversation, conv_id)
        if conversation and conversation.user_id != customer.user_id:
            conversation = None

    if not conversation:
        conv_id = uuid.uuid4()
        conversation = AIConversation(
            id=conv_id,
            user_id=customer.user_id,
            title=user_msg_text[:60],
            created_at=now,
            updated_at=now,
        )
        db.add(conversation)
        await db.flush()
    else:
        conversation.updated_at = now

    # 2. Record user message
    user_msg = AIMessage(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="user",
        content=user_msg_text,
        tool_name=None,
        created_at=now,
    )
    db.add(user_msg)

    # 3. Determine tool and generate domain banking response
    msg_lower = user_msg_text.lower()
    tool_used: str | None = None
    response_text = ""

    if any(k in msg_lower for k in ("spend", "spent", "spending", "expense", "budget")):
        tool_used = "get_spending_summary"
        summary = await customer_service.get_financial_summary(db, customer)
        debits = f"₹{summary.month_to_date_debits:,.2f}"
        credits = f"₹{summary.month_to_date_credits:,.2f}"
        response_text = (
            f"Here is your spending summary for this month:\n\n"
            f"• Total debited / spent: {debits}\n"
            f"• Total credited / deposited: {credits}\n"
            f"• Active accounts: {summary.active_accounts}\n\n"
            f"Would you like to review your largest transactions or see advice on cutting expenses?"
        )

    elif any(k in msg_lower for k in ("balance", "how much money", "account balance", "accounts")):
        tool_used = "get_account_balance"
        accounts = await account_service.list_accounts(db, customer)
        if not accounts:
            response_text = "You currently do not have any active accounts linked to this profile."
        else:
            total_avail = sum((to_money(a.available_balance) for a in accounts), Decimal("0"))
            lines = [f"• {a.account_type.replace('_', ' ').title()} (...{a.account_number[-4:]}): ₹{to_money(a.available_balance):,.2f} (Available)" for a in accounts]
            response_text = (
                f"You have {len(accounts)} account(s) with total available balance of ₹{total_avail:,.2f}:\n\n"
                + "\n".join(lines)
            )

    elif any(k in msg_lower for k in ("loan", "borrow", "eligible", "eligibility", "emi")):
        tool_used = "get_loan_products"
        products = await loan_service.list_products(db)
        if not products:
            response_text = "There are currently no active loan products available in the catalog."
        else:
            lines = [f"• {p.name}: {p.interest_rate}% p.a. (Limits: ₹{to_money(p.min_amount):,.0f} - ₹{to_money(p.max_amount):,.0f})" for p in products[:4]]
            response_text = (
                f"Based on your profile, here are the available loan products:\n\n"
                + "\n".join(lines)
                + f"\n\nYou can apply directly under the Loans section or check detailed EMI calculation anytime."
            )

    elif any(k in msg_lower for k in ("transaction", "statement", "recent", "history", "transfer history")):
        tool_used = "get_recent_transactions"
        # Fetch 5 recent transactions across all customer accounts
        accounts = await account_service.list_accounts(db, customer)
        account_ids = [a.id for a in accounts]
        if not account_ids:
            response_text = "You have no transactions to display."
        else:
            txs = list(
                await db.scalars(
                    select(Transaction)
                    .where(Transaction.account_id.in_(account_ids))
                    .order_by(Transaction.transaction_date.desc())
                    .limit(5)
                )
            )
            if not txs:
                response_text = "No recent transactions found on your accounts."
            else:
                lines = [f"• {t.transaction_date.strftime('%d %b')}: {t.transaction_type} ₹{to_money(t.amount):,.2f} — {t.description or t.merchant_name or 'Transfer'}" for t in txs]
                response_text = "Here are your most recent transactions:\n\n" + "\n".join(lines)

    elif any(k in msg_lower for k in ("recommend", "for you", "advice", "suggestion")):
        tool_used = "get_recommendations"
        recs = await recommendation_service.list_recommendations(db, customer)
        if not recs:
            response_text = "You have no active tailored recommendations at the moment. Keep banking with us to unlock custom insights!"
        else:
            lines = [f"• {r.title}: {r.reason or ''}" for r in recs[:3]]
            response_text = "Here are personalized recommendations curated for you:\n\n" + "\n".join(lines)

    elif any(k in msg_lower for k in ("invest", "portfolio", "wealth", "mutual fund")):
        tool_used = "get_customer_investments"
        investments = list(
            await db.scalars(
                select(CustomerInvestment).where(
                    CustomerInvestment.customer_id == customer.id,
                    CustomerInvestment.status == "ACTIVE",
                )
            )
        )
        if not investments:
            response_text = "You do not have any active investment holdings right now. You can explore fixed deposits and mutual funds in Wealth & Investments."
        else:
            total_inv = sum((to_money(i.amount_invested) for i in investments), Decimal("0"))
            response_text = f"You have {len(investments)} active investment(s) totaling ₹{total_inv:,.2f} invested."

    elif any(k in msg_lower for k in ("profile", "who am i", "kyc", "customer number")):
        tool_used = "get_customer_profile"
        prof = await customer_service.get_profile(db, customer)
        response_text = (
            f"Your Profile Information:\n\n"
            f"• Name: {prof.first_name} {prof.last_name}\n"
            f"• Customer No: {prof.customer_number}\n"
            f"• Segment: {prof.customer_segment or 'Standard'}\n"
            f"• Risk Profile: {prof.risk_profile or 'Moderate'}"
        )

    else:
        response_text = (
            f"Hello {customer.first_name}! I am Credora AI, your personal banking assistant.\n\n"
            f"I can help you with:\n"
            f"• Checking account balances (`Show my balances`)\n"
            f"• Monthly spending breakdown (`How much did I spend this month?`)\n"
            f"• Recent transactions (`Show my recent transactions`)\n"
            f"• Loan products & eligibility (`What loans am I eligible for?`)\n"
            f"• Personal recommendations (`What are my recommendations?`)\n"
            f"• Wealth & investments (`Show my investments`)\n\n"
            f"What would you like to explore today?"
        )

    # 4. Record assistant message
    asst_msg = AIMessage(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        tool_name=tool_used,
        created_at=utcnow(),
    )
    db.add(asst_msg)
    await db.commit()

    return AIChatResponse(
        conversation_id=conversation.id,
        message_id=asst_msg.id,
        response=response_text,
        tool_used=tool_used,
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def get_conversations(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    result = await db.scalars(
        select(AIConversation)
        .where(AIConversation.user_id == customer.user_id)
        .order_by(AIConversation.updated_at.desc())
        .limit(20)
    )
    return [
        ConversationResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in result
    ]


@router.get("/conversations/{conversation_id}", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
) -> list[MessageResponse]:
    conv = await db.get(AIConversation, conversation_id)
    if not conv or conv.user_id != customer.user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    messages = await db.scalars(
        select(AIMessage)
        .where(AIMessage.conversation_id == conversation_id)
        .order_by(AIMessage.created_at.asc())
    )
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            tool_name=m.tool_name,
            created_at=m.created_at,
        )
        for m in messages
    ]
