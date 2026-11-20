import { Navigate, Route, Routes } from "react-router-dom";
import { auth } from "./api/client";
import Layout from "./components/Layout";
import AdminPage from "./pages/AdminPage";
import AnalysisDialog from "./pages/AnalysisDialog";
import CourseDataPage from "./pages/CourseDataPage";
import DashboardPage from "./pages/DashboardPage";
import LevelGapPage from "./pages/LevelGapPage";
import LoginPage from "./pages/LoginPage";
import MatrixPage from "./pages/MatrixPage";
import PostingImportPage from "./pages/PostingImportPage";
import ProgramAnalysisPage from "./pages/ProgramAnalysisPage";
import VersionHistoryPage from "./pages/VersionHistoryPage";

function RequireAuth({ children }: { children: JSX.Element }) {
  return auth.token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<RequireAuth><Layout /></RequireAuth>}>
        <Route index element={<DashboardPage />} />
        <Route path="courses" element={<CourseDataPage />} />
        <Route path="courses/:id/analysis" element={<AnalysisDialog />} />
        <Route path="courses/:id/versions" element={<VersionHistoryPage />} />
        <Route path="matrix" element={<MatrixPage />} />
        <Route path="gaps" element={<LevelGapPage />} />
        <Route path="program" element={<ProgramAnalysisPage />} />
        <Route path="postings" element={<PostingImportPage />} />
        <Route path="admin" element={<AdminPage />} />
      </Route>
    </Routes>
  );
}
