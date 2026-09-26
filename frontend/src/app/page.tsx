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
          <span className="utility-message">
            <span className="tiny-dot" /> A fresh perspective on your financial future
          </span>
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
            Login
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
          <div className="goal-illustration">
            <svg viewBox="0 0 340 260" role="img" aria-label="Saving towards a home: a house surrounded by growing savings and a leafy plant">
              <circle cx="177" cy="128" r="113" fill="#ffffff06" stroke="#ffffff18" />
              <circle cx="177" cy="128" r="91" fill="none" stroke="#ffffff12" />
              <ellipse cx="176" cy="224" rx="126" ry="10" fill="#35124d" opacity=".25" />
              <path d="M97 119 167 57 237 119" fill="none" stroke="#e8c9f6" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M111 116 167 67 223 116V209H111Z" fill="#f5eafa" />
              <path d="M193 78V58H209V93" fill="#c797de" />
              <rect x="150" y="155" width="34" height="54" rx="4" fill="#8850aa" />
              <circle cx="175" cy="184" r="2" fill="#f5eafa" />
              <rect x="131" y="119" width="23" height="23" rx="3" fill="#c4a0da" />
              <rect x="181" y="119" width="23" height="23" rx="3" fill="#c4a0da" />
              <path d="M142.5 119V142M131 130.5H154M192.5 119V142M181 130.5H204" stroke="#f5eafa" strokeWidth="2" />
              {[204, 191, 178].map((y) => <g key={y}><rect x="67" y={y} width="54" height="13" rx="5" fill="#c390dc" /><ellipse cx="94" cy={y} rx="27" ry="7" fill="#e5c3f3" /><path d={`M75 ${y + 9}H113`} stroke="#ad74cb" strokeWidth="1.5" /></g>)}
              {[210, 197].map((y) => <g key={y}><rect x="106" y={y} width="45" height="11" rx="4" fill="#ac78c9" /><ellipse cx="128.5" cy={y} rx="22.5" ry="6" fill="#d7b1e8" /></g>)}
              <path d="M260 199V141" stroke="#e3c5ef" strokeWidth="3" strokeLinecap="round" />
              <path d="M260 177C232 180 231 150 231 150S257 148 260 177Z" fill="#bc8bd2" />
              <path d="M260 161C287 162 287 131 287 131S261 136 260 161Z" fill="#e1c4ee" />
              <path d="M260 145C241 140 246 117 246 117S265 125 260 145Z" fill="#d0a4e3" />
              <path d="M241 195H278L271 221H248Z" fill="#b382cc" />
              <path d="M78 83V95M72 89H84M266 79V91M260 85H272" stroke="#d8b4e9" strokeWidth="2" strokeLinecap="round" />
              <circle cx="281" cy="108" r="3" fill="#d8b4e9" />
            </svg>
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
