import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { api, clearToken } from "../api";

export default function Layout() {
  const [me, setMe] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api("/auth/me").then(setMe).catch(() => {});
  }, []);

  function logout() {
    clearToken();
    navigate("/login");
  }

  return (
    <div className="layout">
      <aside className="side">
        <div className="brand" style={{ fontSize: 28, padding: "4px 12px 18px" }}>
          SmartExpence-IA
        </div>
        <NavLink to="/" end>
          Tablero
        </NavLink>
        <NavLink to="/upload">Subir comprobante</NavLink>
        <NavLink to="/receipts">Libro de gastos</NavLink>
        <div className="grow" />
        <div style={{ padding: 12, fontSize: 13, color: "#d7c9aa" }}>
          {me ? (
            <>
              <div>{me.full_name}</div>
              <div>{me.company_name}</div>
            </>
          ) : (
            "Cargando…"
          )}
        </div>
        <button className="btn ghost" style={{ color: "#f6efdf", borderColor: "#d7c9aa55" }} onClick={logout}>
          Cerrar sesión
        </button>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
