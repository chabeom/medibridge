"use client";

import { Activity, Beaker, ClipboardList, FileSearch, FlaskConical, ShieldCheck } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

type Candidate = {
  name: string;
  rationale: string;
  mechanism: string;
  candidate_type: string;
  overall_score: number;
  safety_summary: string;
  score_breakdown: Record<string, number>;
  warnings: string[];
  approval_status: string;
  approval_reason: string;
};

type ApprovalReview = {
  candidate_name: string;
  status: string;
  reason: string;
  evidence_ids: string[];
};

type Trace = {
  agent: string;
  status: string;
  summary: string;
};

type AnalysisResult = {
  normalized_disease: {
    canonical_name: string;
    confidence: number;
  };
  disease_profile: {
    unmet_need: string;
    mechanisms: string[];
    targets: string[];
    biomarkers: string[];
  };
  candidates: Candidate[];
  approval_reviews: ApprovalReview[];
  evidence: Array<{ id: string; source: string; title: string; summary: string; confidence: number }>;
  clinical_drafts: Array<{
    candidate_name: string;
    phase: string;
    population: string;
    primary_endpoint: string;
    secondary_endpoints: string[];
  }>;
  critic_findings: Array<{ severity: string; category: string; message: string }>;
  agent_trace: Trace[];
  disclaimer: string;
};

const tabs = ["overview", "candidates", "evidence", "clinical", "critic"] as const;
type Tab = (typeof tabs)[number];

const tabLabels: Record<Tab, string> = {
  overview: "개요",
  candidates: "후보",
  evidence: "근거",
  clinical: "임상 설계",
  critic: "비판 검토"
};

const diseaseLabels: Record<string, string> = {
  "Common Cold": "감기",
  Influenza: "독감",
  "COVID-19": "코로나19",
  "Diabetes Mellitus": "당뇨병",
  "Diabetes Mellitus, Type 2": "제2형 당뇨병",
  Hypertension: "고혈압",
  "Migraine Disorders": "편두통",
  Dementia: "치매",
  "Alzheimer Disease": "알츠하이머병",
  "Parkinson Disease": "파킨슨병",
  Asthma: "천식",
  "Pulmonary Disease, Chronic Obstructive": "만성폐쇄성폐질환",
  "Lung Neoplasms": "폐암",
  "Breast Neoplasms": "유방암",
  "Colorectal Neoplasms": "대장암",
  "Stomach Neoplasms": "위암",
  "Liver Neoplasms": "간암",
  "Pancreatic Neoplasms": "췌장암",
  Stroke: "뇌졸중",
  "Arthritis, Rheumatoid": "류마티스 관절염",
  Depression: "우울증",
  Schizophrenia: "조현병",
  "Amyotrophic Lateral Sclerosis": "루게릭병"
};

const agentLabels: Record<string, string> = {
  "Disease Normalizer": "질환명 정규화",
  "Disease Analyst Agent": "질환 분석 에이전트",
  "Evidence Retrieval Agent": "근거 검색 에이전트",
  "Repurposing Hypothesis Agent": "재창출 가설 에이전트",
  "Approval Status Agent": "승인 적응증 필터 에이전트",
  "Safety and Feasibility Agent": "안전성/실현성 에이전트",
  "Scoring Engine": "후보 점수화 엔진",
  "Clinical Design Agent": "임상 설계 에이전트",
  "Citation Validator": "출처 검증기",
  "Critic Agent": "비판 검토 에이전트"
};

const statusLabels: Record<string, string> = {
  complete: "완료",
  warning: "주의",
  needs_data: "추가 데이터 필요"
};

const candidateTypeLabels: Record<string, string> = {
  "investigational repurposing hypothesis": "임상 검토형 재창출 가설",
  "mechanism-based repurposing hypothesis": "기전 기반 재창출 가설",
  "approved comparator or reference candidate": "승인약 기준 후보",
  "symptom-control reference candidate": "증상 조절 기준 후보",
  "broad antiviral repurposing hypothesis": "광범위 항바이러스 재창출 가설",
  "supportive-care comparator or hypothesis": "보조요법 비교/가설 후보",
  "literature-derived repurposing hypothesis": "문헌 기반 재창출 가설"
};

const severityLabels: Record<string, string> = {
  low: "낮음",
  medium: "중간",
  high: "높음"
};

const categoryLabels: Record<string, string> = {
  scope: "해석 범위",
  evidence_gap: "근거 부족",
  candidate_confidence: "후보 신뢰도",
  novelty: "차별성",
  citation: "출처",
  clinical_design: "임상 설계"
};

function displayDiseaseName(canonicalName: string) {
  return diseaseLabels[canonicalName] ?? canonicalName;
}

function summarizeTrace(summary: string) {
  if (summary.startsWith("Canonical disease name:")) {
    const value = summary.replace("Canonical disease name:", "").replace(".", "").trim();
    return `표준 질환명: ${displayDiseaseName(value)}`;
  }

  const exact: Record<string, string> = {
    "Loaded cached evidence from the evidence store.": "캐시된 근거 저장소에서 자료를 불러왔습니다.",
    "Retrieved evidence from PubMed and domestic paper providers, then merged duplicates.":
      "PubMed와 국내 논문 API에서 근거를 병렬 수집하고 중복을 병합했습니다.",
    "No disease-specific evidence passed provider relevance filters.":
      "질환 관련성 필터를 통과한 국내외 근거를 찾지 못했습니다.",
    "Generated mechanism-backed repurposing hypotheses from cached evidence.": "근거 기반 약물 재창출 후보를 생성했습니다.",
    "Filtered candidates that are already approved or standard therapies for the requested disease.":
      "이미 승인되었거나 표준치료로 쓰이는 약물은 재창출 후보에서 제외했습니다.",
    "Added first-pass safety and chemistry feasibility notes.": "1차 안전성 및 기초 물성 검토를 추가했습니다.",
    "Computed weighted candidate ranking.": "가중치 기반 후보 점수를 계산했습니다.",
    "Drafted early clinical feasibility outlines for top candidates.": "상위 후보의 초기 임상 설계 초안을 작성했습니다.",
    "Validated candidate evidence references.": "후보별 근거 출처를 검증했습니다.",
    "Reviewed evidence gaps, novelty, citation integrity, and clinical design readiness.":
      "근거 공백, 차별성, 출처 무결성, 임상 설계 준비도를 검토했습니다.",
    "Reviewed evidence gaps and clinical design readiness.": "근거 공백과 임상 설계 준비도를 검토했습니다."
  };

  if (summary.startsWith("Resolved disease biology for")) {
    return "질환의 생물학적 배경, 타깃, 바이오마커를 정리했습니다.";
  }

  return exact[summary] ?? summary;
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState("질환명을 입력해 분석을 시작하세요");

  const topCandidate = result?.candidates[0];
  const excludedApprovalReviews =
    result?.approval_reviews.filter((review) => review.status === "excluded_approved_or_standard") ?? [];
  const apiUrl = useMemo(() => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000", []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const inputText = query.trim();
    if (!inputText) {
      setNotice("분석할 질환명을 입력하세요");
      return;
    }

    setLoading(true);
    setNotice("분석 중");

    try {
      const response = await fetch(`${apiUrl}/analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json; charset=utf-8" },
        body: JSON.stringify({ input_text: inputText, mode: "live", top_k: 5 })
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const payload = await response.json();
      setResult(payload.result);
      setActiveTab("overview");
      setNotice("백엔드 분석 결과");
    } catch {
      setResult(null);
      setNotice("분석에 실패했습니다. 백엔드 서버와 API 키 상태를 확인하세요");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <section className="workspace">
        <aside className="controlPanel">
          <div className="brand">
            <div className="brandMark">
              <FlaskConical size={22} />
            </div>
            <div>
              <h1>메디브릿지</h1>
              <p>근거 기반 약물 재창출 워크플로우</p>
            </div>
          </div>

          <form className="searchForm" onSubmit={submit}>
            <label htmlFor="disease">질환 또는 세부 환자군</label>
            <input id="disease" value={query} onChange={(event) => setQuery(event.target.value)} />
            <button type="submit" disabled={loading}>
              <FileSearch size={18} />
              <span>{loading ? "분석 중" : "분석하기"}</span>
            </button>
          </form>

          <div className="statusPill">
            <Activity size={16} />
            <span>{notice}</span>
          </div>

          <div className="agentList">
            {result ? (
              result.agent_trace.map((step) => (
                <div className="agentStep" key={`${step.agent}-${step.summary}`}>
                  <span data-status={step.status} />
                  <div>
                    <strong>{agentLabels[step.agent] ?? step.agent}</strong>
                    <p>
                      {statusLabels[step.status] ?? step.status} / {summarizeTrace(step.summary)}
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="agentStep">
                <span data-status="needs_data" />
                <div>
                  <strong>분석 대기</strong>
                  <p>질환명을 입력하면 에이전트 실행 로그가 표시됩니다.</p>
                </div>
              </div>
            )}
          </div>
        </aside>

        <section className="resultPanel">
          {result ? (
            <>
              <header className="resultHeader">
                <div>
                  <p className="eyebrow">표준 질환명</p>
                  <h2>{displayDiseaseName(result.normalized_disease.canonical_name)}</h2>
                </div>
                <div className="confidence">
                  <span>{Math.round(result.normalized_disease.confidence * 100)}%</span>
                  <small>정규화 신뢰도</small>
                </div>
              </header>

              <nav className="tabs" aria-label="분석 결과 탭">
                {tabs.map((tab) => (
                  <button key={tab} className={activeTab === tab ? "active" : ""} onClick={() => setActiveTab(tab)}>
                    {tabLabels[tab]}
                  </button>
                ))}
              </nav>

              {activeTab === "overview" && (
            <section className="tabBody overviewGrid">
              <article className="panelBlock wide">
                <div className="blockTitle">
                  <ShieldCheck size={18} />
                  <h3>미충족 의료 수요</h3>
                </div>
                <p>{result.disease_profile.unmet_need}</p>
              </article>

              <article className="panelBlock">
                <h3>주요 기전</h3>
                <div className="chipGroup">
                  {result.disease_profile.mechanisms.map((item) => (
                    <span key={item}>{item}</span>
                  ))}
                </div>
              </article>

              <article className="panelBlock">
                <h3>타깃/바이오마커</h3>
                <div className="chipGroup">
                  {[...result.disease_profile.targets, ...result.disease_profile.biomarkers].map((item) => (
                    <span key={item}>{item}</span>
                  ))}
                </div>
              </article>

              <article className="panelBlock wide highlight">
                <div className="blockTitle">
                  <Beaker size={18} />
                  <h3>상위 후보</h3>
                </div>
                <strong>{topCandidate?.name ?? "아직 후보가 없습니다"}</strong>
                <p>{topCandidate?.rationale ?? "분석을 실행하면 후보 약물이 생성됩니다."}</p>
              </article>
            </section>
              )}

              {activeTab === "candidates" && (
            <section className="tabBody">
              <div className="candidateTable">
                {result.candidates.length > 0 ? (
                  result.candidates.map((candidate) => (
                    <article className="candidateRow" key={candidate.name}>
                      <div>
                        <strong>{candidate.name}</strong>
                        <p>{candidate.mechanism}</p>
                        <p>{candidate.rationale}</p>
                        <p>{candidate.safety_summary}</p>
                      </div>
                      <span>{candidate.overall_score.toFixed(1)}</span>
                      <small>{candidateTypeLabels[candidate.candidate_type] ?? candidate.candidate_type}</small>
                    </article>
                  ))
                ) : (
                  <article className="panelBlock">
                    <strong>후보 약물이 아직 없습니다</strong>
                    <p>PubMed 근거에서 후보 약물명이 충분히 확인되지 않았습니다. 검색어를 더 구체화하거나 추가 DB 연동 후 다시 검토할 수 있습니다.</p>
                  </article>
                )}
              </div>
              {excludedApprovalReviews.length > 0 && (
                <div className="approvalReview">
                  <h3>제외된 표준치료/기준약물</h3>
                  {excludedApprovalReviews.map((review) => (
                    <article className="panelBlock" key={`${review.candidate_name}-${review.status}`}>
                      <strong>{review.candidate_name}</strong>
                      <p>{review.reason}</p>
                    </article>
                  ))}
                </div>
              )}
            </section>
              )}

              {activeTab === "evidence" && (
            <section className="tabBody evidenceList">
              {result.evidence.length > 0 ? (
                result.evidence.map((item) => (
                  <article className="panelBlock" key={item.id}>
                    <strong>{item.title}</strong>
                    <p>{item.summary}</p>
                    <small>
                      {item.source} / 신뢰도 {Math.round(item.confidence * 100)}%
                    </small>
                  </article>
                ))
              ) : (
                <article className="panelBlock">
                  <strong>근거 데이터가 아직 없습니다</strong>
                  <p>캐시된 근거가 없어서 후보 생성이 보류되었습니다. 다음 단계에서 공개 API 연동으로 채울 영역입니다.</p>
                </article>
              )}
            </section>
              )}

              {activeTab === "clinical" && (
            <section className="tabBody evidenceList">
              {result.clinical_drafts.length > 0 ? (
                result.clinical_drafts.map((draft) => (
                  <article className="panelBlock" key={draft.candidate_name}>
                    <div className="blockTitle">
                      <ClipboardList size={18} />
                      <h3>{draft.candidate_name}</h3>
                    </div>
                    <p>{draft.phase}</p>
                    <p>{draft.population}</p>
                    <strong>{draft.primary_endpoint}</strong>
                    <div className="chipGroup secondaryEndpoints">
                      {draft.secondary_endpoints.map((item) => (
                        <span key={item}>{item}</span>
                      ))}
                    </div>
                  </article>
                ))
              ) : (
                <article className="panelBlock">
                  <strong>임상 설계 초안이 아직 없습니다</strong>
                  <p>후보 약물이 생성되면 대상 환자군, endpoint, 제외/포함 기준 초안을 함께 표시합니다.</p>
                </article>
              )}
            </section>
              )}

              {activeTab === "critic" && (
            <section className="tabBody evidenceList">
              {result.critic_findings.length > 0 ? (
                result.critic_findings.map((finding) => (
                  <article className="panelBlock" key={`${finding.category}-${finding.message}`}>
                    <strong>
                      {severityLabels[finding.severity] ?? finding.severity} /{" "}
                      {categoryLabels[finding.category] ?? finding.category}
                    </strong>
                    <p>{finding.message}</p>
                  </article>
                ))
              ) : (
                <article className="panelBlock">
                  <strong>비판 검토 이슈가 없습니다</strong>
                  <p>현재 결과에서 출처 누락이나 임상 설계 공백이 감지되지 않았습니다.</p>
                </article>
              )}
              <p className="disclaimer">{result.disclaimer}</p>
            </section>
              )}
            </>
          ) : (
            <section className="emptyState">
              <FileSearch size={34} />
              <h2>분석할 질환을 입력하세요</h2>
              <p>초기 데모 결과를 표시하지 않습니다. 질환명을 입력하면 PubMed 기반 근거 검색부터 후보 생성, 임상 설계, 비판 검토까지 실행됩니다.</p>
            </section>
          )}
        </section>
      </section>
    </main>
  );
}
