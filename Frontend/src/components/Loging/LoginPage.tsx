// src/components/Login/LoginPage.tsx
import React from "react";
import { Container, Row, Col } from "react-bootstrap";
import { LoginForm } from "./LoginForm";

interface LoginPageProps {
  onLoginSuccess: (username: string) => void;
}

export const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  return (
    <Container className="vh-100 d-flex justify-content-center align-items-center">
      <Row>
        <Col>
          <LoginForm onLogin={onLoginSuccess} />
        </Col>
      </Row>
    </Container>
  );
};
