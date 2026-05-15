const metrics = [
  ["Active Diagnosis", "7"],
  ["Pending Approval", "3"],
  ["High Risk", "1"],
  ["Evidence Linked", "98%"]
];

export default function HomePage() {
  return (
    <main style={{minHeight: '100vh', background: '#08111f', color: '#e5f2ff', padding: 32, fontFamily: 'Inter, system-ui, sans-serif'}}>
      <section style={{maxWidth: 1180, margin: '0 auto'}}>
        <p style={{color: '#67e8f9', letterSpacing: 2, fontSize: 12}}>FABMIND AGENT</p>
        <h1 style={{fontSize: 44, margin: '12px 0'}}>Load Port / FOUP Clamp Evidence-First AI Troubleshooting</h1>
        <p style={{maxWidth: 780, color: '#a8b3c7', lineHeight: 1.7}}>
          내부망, 읽기 전용, 근거 기반, 사람 승인 구조로 설계된 반도체 장비 트러블슈팅 플랫폼입니다. 단순 챗봇이 아니라 알람, DI/DO, EtherCAT, 매뉴얼, 정비 이력을 하나의 진단 workflow로 연결합니다.
        </p>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginTop: 32}}>
          {metrics.map(([label, value]) => (
            <div key={label} style={{border: '1px solid #1f334f', background: '#0d1b2e', borderRadius: 18, padding: 20}}>
              <div style={{color: '#91a4bd', fontSize: 13}}>{label}</div>
              <div style={{fontSize: 32, fontWeight: 700, marginTop: 8}}>{value}</div>
            </div>
          ))}
        </div>
        <div style={{marginTop: 32, border: '1px solid #1f334f', background: '#0d1b2e', borderRadius: 18, padding: 24}}>
          <h2>Golden Path</h2>
          <ol style={{lineHeight: 2, color: '#c5d3e5'}}>
            <li>LP-01 장비 선택</li>
            <li>LP-CLAMP-014 진단 생성</li>
            <li>Agent Analysis 실행</li>
            <li>Evidence Drawer 확인</li>
            <li>Checklist 수행</li>
            <li>Report 생성 및 Senior 승인</li>
            <li>Audit Log 확인</li>
          </ol>
        </div>
      </section>
    </main>
  );
}
