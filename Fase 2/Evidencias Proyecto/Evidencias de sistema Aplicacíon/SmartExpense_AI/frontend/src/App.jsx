import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { getToken } from "./api";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Receipts from "./pages/Receipts.jsx";
import ReceiptDetail from "./pages/ReceiptDetail.jsx";
import Upload from "./pages/Upload.jsx";

function Private({ children }) {
  const loc = useLocation();
  if (!getToken()) return <Navigate to="/login" replace state={{ from: loc }} />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        element={
          <Private>
            <Layout />
          </Private>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/receipts" element={<Receipts />} />
        <Route path="/receipts/:id" element={<ReceiptDetail />} />
      </Route>
    </Routes>
  );
}
