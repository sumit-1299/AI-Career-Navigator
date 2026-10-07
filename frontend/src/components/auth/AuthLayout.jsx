import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import {
  Compass,
  Search,
  BrainCircuit,
  Target,
  CheckCircle2,
  ShieldCheck,
} from 'lucide-react';

export function AuthLayout() {
  return (
    <div className="min-h-screen bg-slate-950 text-white overflow-hidden">
      <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
        <section className="hidden lg:flex relative p-10 xl:p-14 flex-col justify-between overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(99,102,241,0.35),transparent_30%),radial-gradient(circle_at_85%_85%,rgba(14,165,233,0.20),transparent_30%)]" />

          <div className="relative">
            <Link to="/login" className="inline-flex items-center gap-3">
              <div className="p-2.5 bg-primary-600 rounded-2xl shadow-lg shadow-primary-600/30">
                <Compass className="w-7 h-7" />
              </div>
              <div>
                <p className="font-extrabold text-lg tracking-tight">AI Career Navigator</p>
                <p className="text-xs text-slate-400">Evidence-driven career intelligence</p>
              </div>
            </Link>
          </div>

          <div className="relative max-w-xl">
            <span className="inline-flex text-[11px] uppercase tracking-[0.2em] font-bold text-indigo-300">
              Your next step starts with evidence
            </span>
            <h1 className="mt-5 text-4xl xl:text-6xl font-black leading-[1.02] tracking-tight">
              From live tech jobs
              <br />
              to a clear action plan.
            </h1>
            <p className="mt-6 text-base xl:text-lg leading-7 text-slate-300 max-w-lg">
              Discover technology roles, compare their requirements with your resume and evidence,
              identify skill gaps, and build the next piece of evidence you need.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-10">
              {[
                [Search, 'Find', 'Live tech opportunities'],
                [BrainCircuit, 'Align', 'Semantic job analysis'],
                [Target, 'Act', 'Skill gaps and next steps'],
              ].map(([Icon, title, text]) => (
                <div key={title} className="rounded-2xl border border-white/10 bg-white/[0.06] p-4 backdrop-blur">
                  <Icon className="w-5 h-5 text-indigo-300" />
                  <p className="mt-3 text-sm font-bold">{title}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{text}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="relative flex items-center gap-2 text-xs text-slate-500">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Semantic similarity supports review; it is not a hiring prediction.
          </div>
        </section>

        <section className="bg-slate-50 text-slate-900 flex items-center justify-center p-5 sm:p-8">
          <div className="w-full max-w-md">
            <div className="lg:hidden flex items-center gap-3 mb-8">
              <div className="p-2.5 bg-primary-600 rounded-2xl text-white">
                <Compass className="w-6 h-6" />
              </div>
              <div>
                <p className="font-extrabold tracking-tight">AI Career Navigator</p>
                <p className="text-xs text-slate-500">Evidence-driven career intelligence</p>
              </div>
            </div>

            <Outlet />

            <div className="mt-6 flex items-center justify-center gap-2 text-[11px] text-slate-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Your saved evidence stays tied to your account.
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
