// Boundary: ТүвшнийЗөрүүДэлгэц (proto-06; ФШ-12, 13, 21). Хариуцагч: Б7
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getGaps, listItems } from "../api/courses";
import type { Item, UncoveredClo } from "../api/types";
import { CoursePicker, HistoryBanner, useSelectedCourse, VersionPicker } from "../components/CoursePicker";
import { AddLinkModal } from "../components/LinkModals";
import { Alert, BloomLevel, Button, Empty, GAP, ITEM_TYPE_NAMES, LINK_STATUS, Loading, PageHeader, StatCard, Tag } from "../components/ui";
import { useAsync, useCrumbs } from "../hooks";

const ASSESSMENT = ["lab", "assignment", "exam"];

export default function LevelGapPage() {
  const nav = useNavigate();
  const { courses, course, select, error: cErr, loading: cLoading, versions, version, selectVersion } = useSelectedCourse();
  const vid = version?.id;
  const g = useAsync(() => (vid ? getGaps(vid) : Promise.resolve(null)), [vid]);
  const items = useAsync(() => (vid ? listItems(vid) : Promise.resolve([] as Item[])), [vid]);
  const [adding, setAdding] = useState<UncoveredClo | null>(null);
  useCrumbs(["Түвшний зөрүү", course ? `${course.code} ${course.name}` : "…"]);

  if (cErr) return <Alert>{cErr}</Alert>;
  if (cLoading && !courses.length) return <Loading />;
  if (!course) return <Empty>Хичээл алга. <Link to="/courses">Хичээл нэмэх</Link></Empty>;
  const d = g.data;
  const assessments = (items.data ?? []).filter((i) => ASSESSMENT.includes(i.type));

  return (
    <>
      <PageHeader title="Түвшний зөрүү ба хамрагдаагүй үр дүн"
        subtitle="Блумын шинэчилсэн ангиллаар CLO болон үнэлгээний түвшинг харьцуулсан"
        actions={<>
          <CoursePicker courses={courses} course={course} onSelect={select} />
          <VersionPicker versions={versions} version={version} onSelect={selectVersion} />
        </>} />
      <HistoryBanner version={version} onActive={() => course.active_version && selectVersion(course.active_version.id)} />
      {g.error && <Alert>{g.error}</Alert>}
      {!d ? <Loading /> : (
        <>
          {version?.status === "active" && !course.summary.analyzed && <div style={{ marginBottom: 16 }}><Alert tone="blue">Шинжилгээ хийгдээгүй байна. <Link to={`/courses/${course.id}/analysis`}>Шинжилгээ ажиллуулах</Link></Alert></div>}
          <div className="grid-4">
            <StatCard label="Нийцсэн холбоос" value={d.match} tone="green" />
            <StatCard label="Доогуур түвшин" value={d.below} tone="red" />
            <StatCard label="Дээгүүр түвшин" value={d.above} tone="blue" />
            <StatCard label="Зорилгогүй элемент" value={d.unaligned} tone="yellow" />
          </div>
          <div className="split" style={{ gridTemplateColumns: "minmax(0, 1fr) 440px" }}>
            <div className="card">
              <h3 style={{ marginBottom: 10 }}>Түвшний зөрүүтэй холбоосууд</h3>
              {!d.level_gaps.length ? <Empty>Түвшний зөрүүтэй холбоос алга.</Empty> : (
                <table>
                  <thead><tr><th>CLO</th><th>Үнэлгээний элемент</th><th>Элементийн түвшин</th><th>Зөрүү</th><th /></tr></thead>
                  <tbody>
                    {d.level_gaps.map((x) => (
                      <tr key={x.link_id}>
                        <td className="nowrap"><b>{x.clo.code}</b> <BloomLevel level={x.clo.bloom_level} /></td>
                        <td>{x.item.title}
                          <div className="muted small">{x.item.question_text || x.item.text || ITEM_TYPE_NAMES[x.item.type]}</div></td>
                        <td><BloomLevel level={x.item.bloom_level} /></td>
                        <td><Tag tone={GAP[x.level_gap].tone}>{GAP[x.level_gap].label}</Tag>
                          {x.status !== "confirmed" && <div className="muted small">{LINK_STATUS[x.status].label}</div>}</td>
                        <td><Button small onClick={() => nav(`/matrix?course=${course.id}${version?.status === "history" ? `&version=${version.id}` : ""}&link=${x.link_id}`)}>Харах</Button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            <div className="card">
              <h3 style={{ marginBottom: 12 }}>Хамрагдаагүй CLO</h3>
              {!d.uncovered_clos.length ? <Empty>Бүх CLO баталгаажсан үнэлгээтэй.</Empty> : d.uncovered_clos.map((c) => (
                <div key={c.id} className="uncovered">
                  <div className="row"><b>{c.code}</b><BloomLevel level={c.bloom_level} /></div>
                  <div>{c.text}</div>
                  <div className="muted small">
                    {c.has_proposed ? "Үнэлгээний холбоосын санал байгаа ч баталгаажаагүй." : "Баталгаажсан үнэлгээний холбоос байхгүй."}
                  </div>
                  <div className="row">
                    {version?.status === "active" && <Button small onClick={() => setAdding(c)} disabled={!assessments.length}>Холбоос нэмэх</Button>}
                    {c.has_proposed && <Button small kind="ghost" onClick={() => nav(`/matrix?course=${course.id}${version?.status === "history" ? `&version=${version.id}` : ""}`)}>Санал харах →</Button>}
                  </div>
                </div>
              ))}
              {d.unaligned_items.length > 0 && (
                <>
                  <h3 style={{ margin: "18px 0 10px" }}>Зорилгогүй элемент</h3>
                  {d.unaligned_items.map((i) => (
                    <div key={i.id} className="row" style={{ marginBottom: 8 }}>
                      <Tag>{ITEM_TYPE_NAMES[i.type]}</Tag><span>{i.title}</span><BloomLevel level={i.bloom_level} />
                    </div>
                  ))}
                </>
              )}
              <p className="muted small">Зөвлөмж: «Доогуур» зөрүүтэй CLO-д тохирох түвшний даалгавар нэмэх эсвэл үр дүнгийн үйл үгийг хянах.</p>
            </div>
          </div>
        </>
      )}
      {adding && <AddLinkModal clo={adding} items={assessments} onClose={() => setAdding(null)}
        onSaved={() => { setAdding(null); void g.reload(); }} />}
    </>
  );
}
