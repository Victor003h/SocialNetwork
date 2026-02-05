import AuthPage from "./pages/auth_page";
import MainPage from "./pages/MainPage";
import { authService } from "./services/AuthService";
import { useState } from "react";

export const App: React.FC = () => {
  const [isAuth, setisAuth] = useState<boolean>(authService.isAuthenticated());
  const handleAuthChange = () => {
    setisAuth(true);
  };
  return (
    <>{isAuth ? <MainPage /> : <AuthPage onAuthChange={handleAuthChange} />}</>
  );
};
