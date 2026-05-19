import { AuthGuard } from "@/components/layout/AuthGuard";
import { Sidebar } from "@/components/layout/Sidebar";
import { AuthProvider } from "@/contexts/AuthContext";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <AuthProvider>
        <div className="flex min-h-screen bg-background">
          <Sidebar />
          <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
        </div>
      </AuthProvider>
    </AuthGuard>
  );
}
