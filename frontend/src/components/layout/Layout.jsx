import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Compass,
  LayoutDashboard,
  Briefcase,
  Target,
  Sparkles,
  BookOpen,
  FileText,
  GitCompare,
  TrendingUp,
  User as UserIcon,
  LogOut,
  Menu,
  X,
  FolderGit2,
} from 'lucide-react';

export function Layout() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/jobs', label: 'Find Tech Jobs', icon: Briefcase },
    { to: '/careers', label: 'Careers', icon: Compass },
    { to: '/skill-gap', label: 'Skill Gap & Roadmap', icon: Target },
    { to: '/tasks', label: 'Practical Tasks', icon: FolderGit2 },
    { to: '/skills', label: 'My Skills', icon: Sparkles },
    { to: '/learning', label: 'Learning Pathways', icon: BookOpen },
    { to: '/resume', label: 'Resume Ingestion', icon: FileText },
    { to: '/compare', label: 'Compare Careers', icon: GitCompare },
    { to: '/analytics', label: 'Readiness Velocity', icon: TrendingUp },
    { to: '/profile', label: 'Student Profile', icon: UserIcon },
  ];

  function handleLogout() {
    logout();
    navigate('/login');
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      <aside className="hidden md:flex flex-col w-64 bg-slate-900 text-slate-300 border-r border-slate-800 p-4 sticky top-0 h-screen">
        <div className="flex items-center gap-3 px-2 py-3 mb-6 border-b border-slate-800">
          <div className="p-2 bg-primary-600 rounded-xl text-white shadow-lg shadow-primary-500/30">
            <Compass className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-base text-white tracking-tight leading-tight">
              Career Navigator
            </h1>
            <p className="text-xs text-slate-400">
              Evidence-driven intelligence
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto">
          {navLinks.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                      : 'hover:bg-slate-800/80 hover:text-white text-slate-400'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="pt-4 border-t border-slate-800 mt-auto">
          {isAuthenticated ? (
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-2 overflow-hidden">
                <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-bold text-white shrink-0">
                  {user?.name ? user.name[0].toUpperCase() : 'U'}
                </div>

                <div className="truncate">
                  <p className="text-xs font-semibold text-white truncate">
                    {user?.name || 'Student'}
                  </p>
                  <p className="text-[10px] text-slate-400 truncate">
                    {user?.email}
                  </p>
                </div>
              </div>

              <button
                onClick={handleLogout}
                title="Logout"
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="block text-center py-2 px-3 rounded-lg bg-primary-600 text-white text-xs font-semibold hover:bg-primary-500 transition"
            >
              Sign In
            </NavLink>
          )}
        </div>
      </aside>

      <header className="md:hidden bg-slate-900 text-white p-4 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-primary-600 rounded-lg">
            <Compass className="w-5 h-5" />
          </div>
          <span className="font-bold text-sm tracking-tight">
            AI Career Navigator
          </span>
        </div>

        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 rounded-lg bg-slate-800 text-slate-300"
        >
          {mobileMenuOpen ? (
            <X className="w-5 h-5" />
          ) : (
            <Menu className="w-5 h-5" />
          )}
        </button>
      </header>

      {mobileMenuOpen && (
        <div className="md:hidden bg-slate-900 text-slate-300 border-b border-slate-800 p-4 space-y-1">
          {navLinks.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-slate-400'
                  }`
                }
              >
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}

          {isAuthenticated && (
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-rose-400 hover:bg-slate-800"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          )}
        </div>
      )}

      <main className="flex-1 overflow-y-auto p-4 md:p-8 max-w-7xl mx-auto w-full">
        <Outlet />
      </main>
    </div>
  );
}
