// Boundary: ХянахСамбар (proto-02; UC5, ФШ-13). Хариуцагч: Б6
import { useState } from "react";
import { listCourses } from "../api/courses";
import { useAuth } from "../auth";
import { AddCourseModal, CourseCards, currentAcademicYear } from "../components/CourseCards";
import { Alert, Button, Loading, PageHeader, StatCard } from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";

export default function DashboardPage() {
  useCrumbs(["Хянах самбар"]);
  const { user, hasRole } = useAuth();
  const { data: courses, error, loading, reload } = useAsync(() => listCourses(), []);
  const [adding, setAdding] = useState(false);

  const total = (k: "proposed" | "uncovered_clos" | "level_gaps") =>
    (courses ?? []).reduce((s, c) => s + c.summary[k], 0);

  return (
    <>
      <PageHeader
        title={`Сайн байна уу, ${user?.full_name ?? ""}`}
        subtitle={`${currentAcademicYear()} оны хичээлийн жил`}
        actions={hasRole("teacher") && <Button kind="primary" onClick={() => setAdding(true)}>+ Хичээл нэмэх</Button>}
      />
      {error && <Alert>{error}</Alert>}
      {loading && !courses ? <Loading /> : (
        <>
          <div className="grid-4">
            <StatCard label="Миний хичээл" value={courses?.length ?? 0} />
            <StatCard label="Баталгаажаагүй санал" value={total("proposed")} tone="blue" />
            <StatCard label="Хамрагдаагүй CLO" value={total("uncovered_clos")} tone="red" />
            <StatCard label="Түвшний зөрүү" value={total("level_gaps")} tone="yellow" />
          </div>
          <h3 style={{ marginBottom: 14 }}>Миний хичээлүүд</h3>
          <CourseCards courses={courses ?? []} />
        </>
      )}
      {adding && <AddCourseModal onClose={() => setAdding(false)} onCreated={() => { setAdding(false); void reload(); }} />}
    </>
  );
}
