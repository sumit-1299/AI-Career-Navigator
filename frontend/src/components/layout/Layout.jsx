import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  Compass,
  LayoutDashboard,
  Briefcase,
  GitCompare,
  TrendingUp,
  Search,
  CheckSquare,
  Sparkles,
  BarChart3,
  Layers,
  BookOpen,
  FileText,
  User,
  LogOut,
  LogIn,
  ChevronLeft,
  ChevronRight,
  Menu,
  X,
  Target,
  ExternalLink,
} from 'lucide-react';

export function Layout() {
  const { user, isAuthenticated, logout, targetCareerId, setTargetCareerId } = useAuth();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navGroups = [
    {
      group: 'Overview',
      items: [
        { to: '/', label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      group: 'Career Intelligence',
      items: [
        { to: '/careers', label: 'Career Explorer', icon: Briefcase },
        { to: '/compare', label: 'Compare Careers', icon: GitCompare },
        { to: '/analytics', label: 'Analytics & Trajectory', icon: TrendingUp },
      ],
    },
    {
      group: 'Opportunities & Readiness',
      items: [
        { to: '/jobs', label: 'Job Opportunities', icon: Search },
        { to: '/practical-tasks', label: 'Practical Tasks', icon: CheckSquare },
        { to: '/interview', label: 'Interview Simulator', icon: Sparkles },
      ],
    },
    {
      group: 'Learning & Skills',
      items: [
        { to: '/skill-gap', label: 'Skill Gap Analysis', icon: BarChart3 },
        { to: '/skills', label: 'Verified Skills', icon: Layers },
        { to: '/learning', label: 'Learning Pathways', icon: BookOpen },
      ],
    },
    {
      group: 'Documentation',
      items: [
        { to: '/resume', label: 'Resume ATS Parser', icon: FileText },
      ],
    },
    {
      group: 'Account',
      items: [
        { to: '/profile', label: 'Student Profile', icon: User },
      ],
    },
  ];

  return (
    <div className="min-h-screen bg-canvas flex flex-col antialiased">
      <div className="flex flex-1">
        {/* DESKTOP SIDEBAR */}
        <aside
          className={`hidden md:flex flex-col bg-white border-r border-slate-200/90 transition-all duration-200 ease-in-out shrink-0 sticky top-0 h-screen z-30 ${
            isCollapsed ? 'w-20' : 'w-64'
          }`}
        >
          {/* Brand Header */}
          <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100">
            <NavLink to="/" className="flex items-center gap-3 overflow-hidden">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-600 text-white flex items-center justify-center shrink-0 shadow-subtle">
                <Compass className="w-5 h-5" />
              </div>
              {!isCollapsed && (
                <div className="flex flex-col truncate">
                  <span className="font-extrabold text-sm text-slate-900 tracking-tight leading-none">
                    AI Career Navigator
                  </span>
                  <span className="text-[10px] text-slate-400 font-semibold tracking-wide uppercase mt-1">
                    Student Platform
                  </span>
                </div>
              )}
            </NavLink>
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition"
              title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          </div>

          {/* Nav Links Container */}
          <div className="flex-1 overflow-y-auto p-3 space-y-5">
            {navGroups.map((group, gIdx) => (
              <div key={gIdx} className="space-y-1">
                {!isCollapsed && (
                  <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                    {group.group}
                  </p>
                )}
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.to;
                  return (
                    <NavLink
                      key={item.to}
                      to={item.to}
                      className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-150 ${
                        isActive
                          ? 'bg-primary-50 text-primary-700 shadow-subtle font-bold'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                      }`}
                      title={isCollapsed ? item.label : undefined}
                    >
                      <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-primary-600' : 'text-slate-400'}`} />
                      {!isCollapsed && <span className="truncate">{item.label}</span>}
                    </NavLink>
                  );
                })}
              </div>
            ))}
          </div>

          {/* User / Auth footer */}
          <div className="p-3 border-t border-slate-100 bg-slate-50/50">
            {isAuthenticated ? (
              <div className="flex items-center justify-between">
                {!isCollapsed && (
                  <div className="truncate mr-2">
                    <p className="text-xs font-bold text-slate-800 truncate">{user?.name || 'Student'}</p>
                    <p className="text-[10px] text-slate-400 truncate">{user?.email}</p>
                  </div>
                )}
                <button
                  onClick={handleLogout}
                  className="p-2 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition shrink-0"
                  title="Sign out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <NavLink
                to="/login"
                className="flex items-center justify-center gap-2 w-full py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-semibold shadow-subtle transition"
              >
                <LogIn className="w-4 h-4" />
                {!isCollapsed && <span>Sign In</span>}
              </NavLink>
            )}
          </div>
        </aside>

        {/* MOBILE DRAWER */}
        {mobileOpen && (
          <div className="fixed inset-0 z-50 md:hidden flex">
            <div
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
              onClick={() => setMobileOpen(false)}
            />
            <div className="relative w-72 max-w-[80%] bg-white h-full flex flex-col shadow-2xl z-10 animate-fadeIn">
              <div className="h-16 flex items-center justify-between px-4 border-b border-slate-100">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-primary-600 text-white flex items-center justify-center font-bold">
                    <Compass className="w-5 h-5" />
                  </div>
                  <span className="font-bold text-sm text-slate-900">AI Career Navigator</span>
                </div>
                <button
                  onClick={() => setMobileOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {navGroups.map((group, gIdx) => (
                  <div key={gIdx} className="space-y-1">
                    <p className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1">
                      {group.group}
                    </p>
                    {group.items.map((item) => {
                      const Icon = item.icon;
                      const isActive = location.pathname === item.to;
                      return (
                        <NavLink
                          key={item.to}
                          to={item.to}
                          onClick={() => setMobileOpen(false)}
                          className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold ${
                            isActive
                              ? 'bg-primary-50 text-primary-700 font-bold'
                              : 'text-slate-600 hover:bg-slate-50'
                          }`}
                        >
                          <Icon className={`w-4 h-4 ${isActive ? 'text-primary-600' : 'text-slate-400'}`} />
                          <span>{item.label}</span>
                        </NavLink>
                      );
                    })}
                  </div>
                ))}
              </div>
              <div className="p-4 border-t border-slate-100">
                {isAuthenticated ? (
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center justify-center gap-2 py-2 text-rose-600 bg-rose-50 rounded-xl text-xs font-bold"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Sign Out</span>
                  </button>
                ) : (
                  <NavLink
                    to="/login"
                    onClick={() => setMobileOpen(false)}
                    className="w-full flex items-center justify-center gap-2 py-2 bg-primary-600 text-white rounded-xl text-xs font-bold"
                  >
                    <LogIn className="w-4 h-4" />
                    <span>Sign In</span>
                  </NavLink>
                )}
              </div>
            </div>
          </div>
        )}

        {/* MAIN CONTENT AREA */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* TOP APP BAR */}
          <header className="h-16 bg-white/90 backdrop-blur-md border-b border-slate-200/90 px-4 md:px-8 flex items-center justify-between sticky top-0 z-20">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setMobileOpen(true)}
                className="md:hidden p-2 rounded-xl text-slate-500 hover:bg-slate-100"
              >
                <Menu className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                <span className="hidden sm:inline">Platform</span>
                <span className="hidden sm:inline text-slate-300">/</span>
                <span className="text-slate-900 font-bold capitalize">
                  {location.pathname === '/' ? 'Dashboard' : location.pathname.replace('/', '').replace('-', ' ')}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-primary-50 text-primary-700 flex items-center justify-center font-bold text-xs border border-primary-200/60">
                    {user?.name ? user.name[0].toUpperCase() : 'U'}
                  </div>
                  <span className="hidden sm:inline text-xs font-bold text-slate-700">
                    {user?.name || 'Student'}
                  </span>
                </div>
              ) : (
                <NavLink
                  to="/login"
                  className="px-3.5 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-xl text-xs font-bold transition shadow-subtle"
                >
                  Sign In
                </NavLink>
              )}
            </div>
          </header>

          {/* PAGE CONTENT */}
          <main className="flex-1 p-4 md:p-8 max-w-7xl mx-auto w-full">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}

export default Layout;
