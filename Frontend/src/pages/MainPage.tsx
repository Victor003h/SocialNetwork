import { useEffect, useState } from "react";
import BottomNav from "../components/BottomNav";
import { PageID } from "../types/nav.types";
import ProfileSection from "../components/Profile";
import Feed from "../components/Feed";
import SearchUser from "../components/SearchUser";
import AdminPanel from "../components/AdminPanel";
import { authService } from "../services/AuthService";
import { presenceService } from "../services/PresenceService";

const HEARTBEAT_MS = 15000;

interface MainPageProps {
  onLogout: () => void;
}

const MainPage: React.FC<MainPageProps> = ({ onLogout }) => {
  const [activePage, setActivePage] = useState<PageID>("feed");
  const isAdmin = authService.isAdmin();

  // Heartbeat de presencia mientras hay sesión activa.
  useEffect(() => {
    presenceService.ping();
    const interval = setInterval(() => presenceService.ping(), HEARTBEAT_MS);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="d-flex flex-column min-vh-100 position-relative bg-dark">
      <main className="flex-grow-1" style={{ paddingBottom: "80px" }}>
        {activePage === "feed" && <Feed />}
        {activePage === "profile" && <ProfileSection onLogout={onLogout} />}
        {activePage === "search" && <SearchUser />}
        {activePage === "admin" && isAdmin && <AdminPanel />}
      </main>

      <BottomNav
        activePage={activePage}
        onPageChange={setActivePage}
        showAdmin={isAdmin}
      />
    </div>
  );
};

export default MainPage;
