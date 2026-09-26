import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  ArrowDownLeft,
  Sparkles,
  ShieldCheck,
  Wallet,
  TrendingUp,
  Fingerprint,
  ChevronRight,
  CircleCheck,
  Globe2,
} from "lucide-react";
import { Brand } from "@/components/ui";

export default function Landing() {
  return (
    <div className="landing">
      <div className="announcement">
        <div className="container utility-inner">
          <span className="utility-message"><span className="tiny-dot" /> A fresh perspective on your financial future</span>
          <Link className="staff-login" href="/admin/login"><ShieldCheck size={14} /> Admin login <ArrowUpRight size={13} /></Link>
        </div>
      </div>
      <header className="landing-header container">
        <Brand />
        <nav aria-label="Main navigation">
          <a href="#banking">Everyday banking</a>
          <a href="#future">Grow your wealth</a>
          <a href="#intelligence">Why Credora?</a>
        </nav>
        <div className="landing-auth-actions" role="group" aria-label="Customer access">
          <Link className="customer-login" href="/login">
            Customer login
          </Link>
          <Link className="customer-signup" href="/register">
            Sign up <ArrowRight size={16} />
          </Link>
        </div>
      </header>
      <main id="main">
        <section className="hero container">
          <div className="hero-copy">
            <h1>
              Banking, a little
              <br />
              more <span>personal.</span>
            </h1>
            <p>
              Life doesn’t stand still. Neither should your bank.
              <br className="desktop-break" /> Meet everyday banking that
              understands you, helps you
              <br className="desktop-break" /> grow, and puts your future first.
            </p>
            <div className="hero-actions">
              <Link href="/register" className="button">
                Start your journey <ArrowUpRight size={18} />
              </Link>
              <Link href="/register" className="button secondary">
                Explore banking <ArrowRight size={17} />
              </Link>
            </div>
            <div className="hero-proof">
              <span>
                <ShieldCheck size={17} /> Thoughtful security
              </span>
              <span>
                <CircleCheck size={17} /> All in one place
              </span>
            </div>
          </div>
          <div
            className="hero-art"
            aria-label="Illustration of the Credora sample banking experience"
          >
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="art-spark spark-one">✦</div>
            <div className="art-spark spark-two">✧</div>
            <div className="floating-insight">
              <span className="icon-tile lavender">
                <Sparkles size={19} />
              </span>
              <div>
                <strong>A little insight. A big difference.</strong>
                <small>You saved 12% more this month.</small>
              </div>
              <span className="insight-dot" />
            </div>
            <div className="bank-card">
              <div className="card-top">
                <span className="card-brand">credora.</span>
                <span>EVERYDAY BANKING</span>
              </div>
              <div className="card-chip">
                <span />
                <span />
              </div>
              <div className="card-number">
                •••• &nbsp; •••• &nbsp; •••• &nbsp; 4821
              </div>
              <div className="card-bottom">
                <div>
                  <small>YOUR NEXT CHAPTER</small>
                  <span>STARTS HERE</span>
                </div>
                <span className="card-circles">
                  <i />
                  <i />
                </span>
              </div>
            </div>
            <div className="balance-float">
              <span className="muted">
                Your total balance <Wallet size={15} />
              </span>
              <strong>
                ₹2,46,950<span>.00</span>
              </strong>
              <div className="balance-bottom">
                <span>
                  <TrendingUp size={13} /> 8.2% this month
                </span>
                <div className="mini-bars">
                  {[18, 29, 24, 38, 32, 49, 42, 58].map((h, i) => (
                    <i style={{ height: h }} key={i} />
                  ))}
                </div>
              </div>
            </div>
            <div className="transfer-float">
              <span className="icon-tile green">
                <ArrowDownLeft size={20} />
              </span>
              <div>
                <strong>Salary received</strong>
                <small>A good start to your month</small>
              </div>
              <b>+ ₹65,000</b>
            </div>
            <span className="art-caption">
              A glimpse of your financial everyday · Sample data
            </span>
          </div>
        </section>
        <section
          className="benefit-strip container"
          aria-label="Platform benefits"
        >
          <div>
            <Fingerprint />
            <span>
              <strong>Security, built in</strong>
              <small>Your peace of mind comes first</small>
            </span>
          </div>
          <div>
            <Wallet />
            <span>
              <strong>One connected view</strong>
              <small>Less switching. More clarity.</small>
            </span>
          </div>
          <div>
            <Sparkles />
            <span>
              <strong>Intelligence that helps</strong>
              <small>Insights made for your everyday</small>
            </span>
          </div>
          <div>
            <Globe2 />
            <span>
              <strong>Wherever life takes you</strong>
              <small>Your banking, on your terms</small>
            </span>
          </div>
        </section>
        <section id="banking" className="landing-section container">
          <div className="section-heading">
            <div>
              <span className="eyebrow">
                SIMPLER DAYS. BIGGER POSSIBILITIES.
              </span>
              <h2>
                Everything you need.
                <br />
                Right where you need it.
              </h2>
            </div>
            <p className="muted section-description">
              From your first coffee to your next big milestone,
              <br />
              make every money move feel a little easier.
            </p>
          </div>
          <div className="feature-grid">
            {[
              {
                icon: Wallet,
                tag: "EVERYDAY BANKING",
                title: "Life moves. So can your money.",
                text: "Accounts, payments and transfers. All the essentials, beautifully connected.",
                href: "/register",
                link: "Discover your accounts",
              },
              {
                icon: TrendingUp,
                tag: "YOUR FINANCIAL FUTURE",
                title: "Small steps. Meaningful growth.",
                text: "Explore investments and find space for the things you’re working towards.",
                href: "/register",
                link: "Explore wealth",
              },
              {
                icon: Sparkles,
                tag: "PERSONAL INTELLIGENCE",
                title: "See the bigger picture. Clearly.",
                text: "Understand your spending, spot patterns and plan your next move with confidence.",
                href: "/register",
                link: "Meet your money insights",
              },
            ].map((item) => (
              <Link className="feature-card" key={item.tag} href={item.href}>
                <span className="icon-tile lavender">
                  <item.icon size={25} />
                </span>
                <span className="eyebrow">{item.tag}</span>
                <h3>{item.title}</h3>
                <p>{item.text}</p>
                <span className="feature-link">
                  {item.link}
                  <ArrowUpRight size={19} />
                </span>
              </Link>
            ))}
          </div>
        </section>
        <section id="intelligence" className="intelligence-section container">
          <div className="insight-preview">
            <h3>
              A healthier relationship
              <br />
              with your money.
            </h3>
            <div className="insight-chart">
              {[42, 65, 52, 78, 61, 90].map((h, i) => (
                <div key={i}>
                  <span style={{ height: h }} />
                  <small>{["Apr", "May", "Jun", "Jul", "Aug", "Sep"][i]}</small>
                </div>
              ))}
            </div>
            <div className="insight-foot">
              <span className="icon-tile green">
                <TrendingUp size={18} />
              </span>
              <span>
                <strong>Progress looks good on you.</strong>
                <small>Discover patterns in your financial life.</small>
              </span>
            </div>
          </div>
          <div>
            <span className="eyebrow">
              A LITTLE INTELLIGENCE GOES A LONG WAY
            </span>
            <h2>
              More than a balance.
              <br />A better understanding.
            </h2>
            <p className="muted">
              Turn your everyday transactions into a clearer picture of your
              finances. With useful insights and a personal banking assistant,
              your next step is easier to see.
            </p>
            <ul className="check-list">
              <li>
                <CircleCheck /> Spending insights that make sense
              </li>
              <li>
                <CircleCheck /> Recommendations around your goals
              </li>
              <li>
                <CircleCheck /> A helping hand, just a conversation away
              </li>
            </ul>
            <Link className="text-link" href="/register">
              See your financial overview <ArrowRight size={17} />
            </Link>
          </div>
        </section>
        <section id="future" className="future-banner container">
          <div>
            <span className="eyebrow">YOUR NEXT CHAPTER STARTS HERE</span>
            <h2>
              Big dreams.
              <br />
              Meet everyday possibilities.
            </h2>
            <p>
              A home of your own. A new adventure. A little more freedom.
              <br />
              Let’s make room for what matters to you.
            </p>
            <Link className="button white" href="/register">
              Explore your possibilities <ArrowUpRight size={18} />
            </Link>
          </div>
          <div className="future-art" aria-hidden="true">
            <span>
              your
              <br />
              <i>next.</i>
            </span>
            <ArrowUpRight />
          </div>
        </section>
        <section className="closing container">
          <div>
            <h2>A fresh start for your finances.</h2>
            <p className="muted">
              Your everyday. Your ambitions. Your kind of banking.
            </p>
          </div>
          <Link className="button" href="/register">
            Let’s get started <ChevronRight size={17} />
          </Link>
        </section>
      </main>
      <footer className="landing-footer">
        <div className="container">
          <div className="footer-top">
            <Brand />
            <p>
              Personal Banking Intelligence Platform.
              <br />
              Built around you.
            </p>
            <a href="#banking">Banking</a>
            <a href="#intelligence">Our approach</a>
            <Link href="/login">Customer login</Link>
          </div>
          <div className="footer-bottom">
            <span>
              © 2026 Credora. An independent academic banking prototype.
            </span>
            <span>
              Sample experience · No real money movement · Not affiliated with
              SBI
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
