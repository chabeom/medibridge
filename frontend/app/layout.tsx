import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "메디브릿지",
  description: "근거 기반 약물 재창출 가설 생성 워크플로우"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
