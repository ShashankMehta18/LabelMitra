import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import Scan from "./pages/Scan";
import Result from "./pages/Result";
import Consumer from "./pages/consumer";
import ConsumerResult from "./pages/consumerResult";

export default function App() {
  return (
    <Layout>
      <Routes>
        {/* Dashboard */}
        <Route path="/" element={<Home />} />

        {/* Inspector Panel */}
        <Route path="/scan" element={<Scan />} />
        <Route path="/result" element={<Result />} />

        {/* Consumer Panel */}
        <Route path="/consumer" element={<Consumer />} />
        <Route path="/consumer/result" element={<ConsumerResult />} />

        {/* Old Quality URL → Consumer Panel */}
        <Route
          path="/quality"
          element={<Navigate to="/consumer" replace />}
        />

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}