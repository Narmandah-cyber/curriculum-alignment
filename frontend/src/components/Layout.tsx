// Figma-гийн Sidebar, TopBar компонент (бүх дэлгэцийн нэгдсэн бүтэц, Бүлэг 3 «Прототип»). Хариуцагч: Б1.
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { ROLE_NAMES, useAuth } from "../auth";
import { CrumbContext } from "../hooks";

const link = ({ isActive }: { isActive: boolean }) => (isActive ? "active" : "");

function initials(name: string) {
  return name.split(/[\s.]+/).filter(Boolean).map((p) => p[0]).join("").slice(0, 2).toUpperCase();
}

export default function Layout() {
  const { user, hasRole, logout } = useAuth();
  const [crumbs, setCrumbs] = useState<string[]>([]);
  const role = user?.roles.includes("teacher") ? "teacher" : user?.roles[0];

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="brand"><span className="logo" /> Уялдаа</div>
        <NavLink to="/" end className={link}>Хянах самбар</NavLink>
        <NavLink to="/courses" className={link}>Миний хичээлүүд</NavLink>
        <NavLink to="/matrix" className={link}>Хамрах хүрээ</NavLink>
        <NavLink to="/gaps" className={link}>Түвшний зөрүү</NavLink>
        {hasRole("coordinator", "admin") && (
          <>
            <div className="label">Хөтөлбөрийн түвшин</div>
            <NavLink to="/program" className={link}>Хөтөлбөр</NavLink>
            <NavLink to="/postings" className={link}>Ажлын зарлал</NavLink>
            <NavLink to="/reports" className={link}>Тайлан</NavLink>
          </>
        )}
        {hasRole("admin") && (
          <>
            <div className="label">Систем</div>
            <NavLink to="/admin" className={link}>Тохиргоо</NavLink>
          </>
        )}
      </nav>
      <div className="main">
        <header className="topbar">
          <span className="crumbs">{crumbs.length ? crumbs.join(" / ") : "Уялдаа"}</span>
          {user && (
            <span className="user">
              {role && <span className="tag">{ROLE_NAMES[role]}</span>}
              <span className="avatar">{initials(user.full_name)}</span>
              <span className="user-name">{user.full_name}</span>
              <button className="link-btn" onClick={logout}>Гарах</button>
            </span>
          )}
        </header>
        <main className="content">
          <CrumbContext.Provider value={setCrumbs}>
            <Outlet />
          </CrumbContext.Provider>
        </main>
      </div>
    </div>
  );
}
