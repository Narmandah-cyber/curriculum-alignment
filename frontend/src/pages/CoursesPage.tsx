// Boundary: Миний хичээлүүд (proto-02-ийн хичээлийн жагсаалт; UC2). Хариуцагч: Б6
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { listCourses } from "../api/courses";
import { useAuth } from "../auth";
import { AddCourseModal, CourseCards } from "../components/CourseCards";
import { Alert, Button, Loading, PageHeader } from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";

export default function CoursesPage() {
  useCrumbs(["Миний хичээлүүд"]);
  const nav = useNavigate();
  const { hasRole } = useAuth();
  const viewer = hasRole("coordinator", "admin");
  const [all, setAll] = useState(false);
  const { data, error, loading } = useAsync(() => listCourses(!all), [all]);
  const [adding, setAdding] = useState(false);

  return (
    <>
      <PageHeader title="Миний хичээлүүд" subtitle="Хичээлийн CLO, сургалтын элемент, шинжилгээ"
        actions={<>
          {viewer && <Button onClick={() => setAll(!all)}>{all ? "Зөвхөн миний" : "Бүх хичээл"}</Button>}
          {hasRole("teacher") && <Button kind="primary" onClick={() => setAdding(true)}>+ Хичээл нэмэх</Button>}
        </>} />
      {error && <Alert>{error}</Alert>}
      {loading && !data ? <Loading /> : <CourseCards courses={data ?? []} />}
      {adding && <AddCourseModal onClose={() => setAdding(false)} onCreated={(c) => nav(`/courses/${c.id}`)} />}
    </>
  );
}
