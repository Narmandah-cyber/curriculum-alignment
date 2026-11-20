import { NavLink, Outlet } from "react-router-dom";

const link = ({ isActive }: { isActive: boolean }) => (isActive ? "active" : "");

export default function Layout() {
  return (
    <div className="layout">
      <nav className="sidebar">
        <h1>Уялдаа</h1>
        <NavLink to="/" end className={link}>Хянах самбар</NavLink>
        <NavLink to="/courses" className={link}>Миний хичээлүүд</NavLink>
        <NavLink to="/matrix" className={link}>Хамрах хүрээ</NavLink>
        <NavLink to="/gaps" className={link}>Түвшний зөрүү</NavLink>
        <div className="label">Хөтөлбөрийн түвшин</div>
        <NavLink to="/program" className={link}>Хөтөлбөр</NavLink>
        <NavLink to="/postings" className={link}>Ажлын зарлал</NavLink>
        <div className="label">Систем</div>
        <NavLink to="/admin" className={link}>Тохиргоо</NavLink>
      </nav>
      <div className="main">
        <header className="topbar"><span>Уялдаа</span><span>{/* TODO(Б1): хэрэглэгчийн нэр, үүрэг */}</span></header>
        <main className="content"><Outlet /></main>
      </div>
    </div>
  );
}
