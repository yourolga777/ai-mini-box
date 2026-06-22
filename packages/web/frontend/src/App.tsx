import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Contacts from "./pages/Contacts";
import Products from "./pages/Products";
import Messages from "./pages/Messages";
import Orders from "./pages/Orders";
import Plugins from "./pages/Plugins";
import PluginDetail from "./pages/PluginDetail";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="contacts" element={<Contacts />} />
          <Route path="products" element={<Products />} />
          <Route path="messages" element={<Messages />} />
          <Route path="orders" element={<Orders />} />
          <Route path="plugins" element={<Plugins />} />
          <Route path="plugins/:name" element={<PluginDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
