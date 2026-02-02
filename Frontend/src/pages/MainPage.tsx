import { useState } from "react";
import BottomNav from "../components/BottomNav";
import { PageID } from "../types/nav.types";
import ProfileSection from "../components/Profile"; // Importar
import Feed from "../components/Feed";

const MainPage: React.FC = () => {
  const [activePage, setActivePage] = useState<PageID>("profile");

  return (
    // Añadimos clases de Bootstrap para asegurar el alto total y posición relativa
    <div className="d-flex flex-column min-vh-100 position-relative bg-dark">
      <main className="flex-grow-1" style={{ paddingBottom: "80px" }}>
        {activePage === "feed" && <Feed />}
        {activePage === "profile" && <ProfileSection />}
      </main>

      <BottomNav activePage={activePage} onPageChange={setActivePage} />
    </div>
  );
};

export default MainPage;
