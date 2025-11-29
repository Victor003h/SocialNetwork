// src/App.tsx
//import React, { useState } from "react";
//import { LoginPage } from "./components/Loging/LoginPage";
import { NetworkPage } from "./components/Network/NetworkPage";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap/dist/js/bootstrap.bundle.min.js";

export const App: React.FC = () => {
  //const [user, setUser] = useState<string | null>(null);

  //return user ? (
  //  <NetworkPage />
  //) : (
  //  <LoginPage onLoginSuccess={(username: string) => setUser(username)} />
  //);
  return <NetworkPage />;
};
