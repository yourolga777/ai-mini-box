import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Calendar from "./pages/Calendar";
import ContactDetail from "./pages/ContactDetail";
import Contacts from "./pages/Contacts";
import Products from "./pages/Products";
import KnowledgeBase from "./pages/KnowledgeBase";
import MessageDetail from "./pages/MessageDetail";
import Messages from "./pages/Messages";
import Orders from "./pages/Orders";
import OrderDetail from "./pages/OrderDetail";
import Plugins from "./pages/Plugins";
import PluginDetail from "./pages/PluginDetail";
import EmailSettings from "./pages/EmailSettings";
import BusinessSettings from "./pages/BusinessSettings";
import Templates from "./pages/Templates";
import Help from "./pages/Help";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="calendar" element={<Calendar />} />
          <Route path="contacts" element={<Contacts />} />
          <Route path="contacts/:id" element={<ContactDetail />} />
          <Route path="products" element={<Products />} />
          <Route path="messages" element={<Messages />} />
          <Route path="messages/:id" element={<MessageDetail />} />
          <Route path="orders" element={<Orders />} />
          <Route path="orders/:id" element={<OrderDetail />} />
          <Route path="plugins" element={<Plugins />} />
          <Route path="plugins/:name" element={<PluginDetail />} />
          <Route path="email" element={<EmailSettings />} />
          <Route path="settings/templates" element={<Templates />} />
          <Route path="settings/business" element={<BusinessSettings />} />
          <Route path="knowledge-base" element={<KnowledgeBase />} />
          <Route path="help" element={<Help />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
