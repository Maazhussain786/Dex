import {
  Activity,
  Bot,
  Braces,
  Bug,
  CircleDot,
  Clock3,
  FileText,
  Gauge,
  GitBranch,
  Globe2,
  KeyRound,
  Network,
  Play,
  Search,
  ShieldAlert,
  Waypoints
} from "lucide-react";

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const agents = [
  { name: "Coordinator", state: "Planning", color: "text-mint" },
  { name: "UI", state: "Queued", color: "text-brass" },
  { name: "Navigation", state: "Queued", color: "text-brass" },
  { name: "Network", state: "Queued", color: "text-brass" },
  { name: "Security", state: "Idle", color: "text-zinc-400" }
];

const endpoints = [
  { method: "POST", path: "/login", category: "Authentication" },
  { method: "GET", path: "/profile", category: "User data" },
  { method: "POST", path: "/files/upload", category: "Upload" }
];

const graphRows = [
  ["Login Page", "submits", "POST /login"],
  ["JWT Token", "unlocks", "Dashboard"],
  ["Dashboard", "loads", "GET /profile"],
  ["Profile", "renders", "Avatar Upload"]
];

const reports = ["Architecture", "API", "Security", "Performance", "Onboarding"];

function Metric({
  icon: Icon,
  label,
  value,
  tone
}: {
  icon: typeof Activity;
  label: string;
  value: string;
  tone: string;
}) {
  return (
    <div className="rounded-md border border-line bg-panel/80 p-4">
      <div className="flex items-center gap-2 text-sm text-zinc-400">
        <Icon className={tone} size={17} aria-hidden="true" />
        <span>{label}</span>
      </div>
      <div className="mt-3 text-2xl font-semibold text-white">{value}</div>
    </div>
  );
}

function Panel({
  title,
  icon: Icon,
  children,
  action
}: {
  title: string;
  icon: typeof Activity;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <section className="rounded-md border border-line bg-panel/85 p-4 shadow-2xl shadow-black/10">
      <div className="mb-4 flex min-h-8 items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Icon size={18} className="text-mint" aria-hidden="true" />
          <h2 className="text-sm font-semibold uppercase text-zinc-200">{title}</h2>
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export default function Dashboard() {
  return (
    <main className="min-h-screen px-5 py-5 lg:px-7">
      <header className="mb-5 flex flex-col gap-4 border-b border-line pb-5 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-md bg-mint text-ink">
              <Bot size={22} aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-white">Dex</h1>
              <p className="text-sm text-zinc-400">Autonomous software understanding workspace</p>
            </div>
          </div>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="relative block min-w-72">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"
              size={17}
              aria-hidden="true"
            />
            <input
              className="h-10 w-full rounded-md border border-line bg-[#11151c] pl-10 pr-3 text-sm text-zinc-100"
              defaultValue="https://example-app.local"
              aria-label="Target application URL"
            />
          </label>
          <button className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-mint px-4 text-sm font-semibold text-ink">
            <Play size={17} aria-hidden="true" />
            Start Exploration
          </button>
        </div>
      </header>

      <section className="mb-5 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric icon={Waypoints} label="Routes mapped" value="14" tone="text-mint" />
        <Metric icon={Network} label="APIs classified" value="9" tone="text-brass" />
        <Metric icon={ShieldAlert} label="Security signals" value="3" tone="text-coral" />
        <Metric icon={Clock3} label="Runtime evidence" value="126" tone="text-violet" />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.35fr_1fr]">
        <Panel
          title="Live Browser Session"
          icon={Globe2}
          action={<span className="rounded-md bg-[#10251f] px-2 py-1 text-xs text-mint">Connected</span>}
        >
          <div className="grid min-h-[390px] grid-rows-[auto_1fr] overflow-hidden rounded-md border border-line bg-[#0b0e13]">
            <div className="flex h-10 items-center gap-2 border-b border-line px-3">
              <CircleDot className="text-coral" size={12} aria-hidden="true" />
              <CircleDot className="text-brass" size={12} aria-hidden="true" />
              <CircleDot className="text-mint" size={12} aria-hidden="true" />
              <span className="ml-3 truncate text-xs text-zinc-500">Target runtime preview</span>
            </div>
            <div className="grid place-items-center p-8 text-center">
              <div className="max-w-md">
                <Activity className="mx-auto mb-4 text-mint" size={38} aria-hidden="true" />
                <p className="text-lg font-semibold text-white">Explorer waiting for backend events</p>
                <p className="mt-2 text-sm leading-6 text-zinc-400">
                  The browser stream will show screenshots, DOM states, console signals, and action history
                  as the Playwright runner starts collecting evidence.
                </p>
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="Agent Runtime" icon={Bot}>
          <div className="space-y-3">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className="flex items-center justify-between rounded-md border border-line bg-[#11151c] px-3 py-3"
              >
                <span className="text-sm font-medium text-zinc-100">{agent.name}</span>
                <span className={`text-xs font-semibold ${agent.color}`}>{agent.state}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 rounded-md border border-line bg-[#11151c] p-3 text-sm text-zinc-400">
            API base: <span className="text-zinc-200">{apiBaseUrl}</span>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Knowledge Graph" icon={GitBranch}>
          <div className="space-y-2">
            {graphRows.map(([from, relation, to]) => (
              <div key={`${from}-${to}`} className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 text-xs">
                <span className="rounded-md border border-line bg-[#11151c] px-2 py-2 text-zinc-100">{from}</span>
                <span className="text-zinc-500">{relation}</span>
                <span className="rounded-md border border-line bg-[#11151c] px-2 py-2 text-zinc-100">{to}</span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="API Explorer" icon={Braces}>
          <div className="space-y-2">
            {endpoints.map((endpoint) => (
              <div key={endpoint.path} className="rounded-md border border-line bg-[#11151c] p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-xs font-semibold text-mint">{endpoint.method}</span>
                  <span className="truncate text-sm text-zinc-100">{endpoint.path}</span>
                </div>
                <p className="mt-2 text-xs text-zinc-500">{endpoint.category}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Risk And Performance" icon={Gauge}>
          <div className="grid gap-3">
            <div className="rounded-md border border-line bg-[#11151c] p-3">
              <div className="flex items-center gap-2 text-sm text-coral">
                <KeyRound size={16} aria-hidden="true" />
                Auth storage review pending
              </div>
              <p className="mt-2 text-xs leading-5 text-zinc-500">
                Security agent will inspect cookies, local storage, headers, and token handling.
              </p>
            </div>
            <div className="rounded-md border border-line bg-[#11151c] p-3">
              <div className="flex items-center gap-2 text-sm text-brass">
                <Bug size={16} aria-hidden="true" />
                Waterfall analysis queued
              </div>
              <p className="mt-2 text-xs leading-5 text-zinc-500">
                Performance agent will flag duplicate requests and slow route transitions.
              </p>
            </div>
          </div>
        </Panel>
      </section>

      <section className="mt-4 grid gap-4 xl:grid-cols-[1fr_1.35fr]">
        <Panel title="Documentation" icon={FileText}>
          <div className="grid grid-cols-2 gap-2">
            {reports.map((report) => (
              <button
                key={report}
                className="rounded-md border border-line bg-[#11151c] px-3 py-3 text-left text-sm text-zinc-200"
              >
                {report}
              </button>
            ))}
          </div>
        </Panel>

        <Panel title="Reasoning Panel" icon={Network}>
          <div className="rounded-md border border-line bg-[#11151c] p-4">
            <p className="text-sm text-zinc-300">Question</p>
            <p className="mt-2 text-lg font-semibold text-white">What happens after login?</p>
            <div className="mt-4 border-l-2 border-mint pl-4 text-sm leading-6 text-zinc-400">
              Dex will answer from graph neighbors, captured API calls, route transitions, and evidence IDs once
              exploration data is available.
            </div>
          </div>
        </Panel>
      </section>
    </main>
  );
}
