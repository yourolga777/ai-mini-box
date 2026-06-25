import { NavLink, Outlet } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/calendar", label: "Calendar" },
  { to: "/contacts", label: "Contacts" },
  { to: "/products", label: "Products" },
  { to: "/messages", label: "Messages" },
  { to: "/orders", label: "Orders" },
  { to: "/plugins", label: "Plugins" },
  { to: "/knowledge-base", label: "Knowledge Base" },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <nav className="w-56 bg-gray-900 text-white p-4 flex flex-col gap-1">
        <div className="text-lg font-bold mb-4 px-3">AI mini box</div>
        {links.map((l) => (
          <NavLink
            key={l.to}
            to={l.to}
            end={l.to === "/"}
            className={({ isActive }) =>
              `px-3 py-2 rounded transition ${isActive ? "bg-blue-600" : "hover:bg-gray-700"}`
            }
          >
            {l.label}
          </NavLink>
        ))}
        <div className="mt-auto pt-4 border-t border-gray-700">
          <NavLink
            to="/help"
            end
            className={({ isActive }) =>
              `px-3 py-2 rounded transition ${isActive ? "bg-blue-600" : "hover:bg-gray-700"}`
            }
          >
            Help
          </NavLink>
        </div>
      </nav>
      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
