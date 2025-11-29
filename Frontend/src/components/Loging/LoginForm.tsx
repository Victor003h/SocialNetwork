// src/components/Login/LoginForm.tsx
import React, { useState } from "react";
import { Form, Card, Button } from "react-bootstrap";
import RegisterModal from "./Modal_Register";
import { LoginData } from "../../types/LoginData";
import handleLogin from "./HandleLogin";
interface LoginFormProps {
  onLogin: (username: string) => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onLogin }) => {
  const [UserAccount, setUserAccount] = useState<LoginData>({
    username: "",
    password: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleLogin.login(UserAccount).then((response) => {
      if (response.ok) {
        alert("Inicio de sesión exitoso.");
        onLogin(UserAccount.username);
      } else {
        alert(`Error: ${response.message}`);
      }
    });
  };

  return (
    <Card className="p-4 shadow-sm">
      <Card.Header className="text-center bg-white border-0">
        <Card.Title className="h4">Iniciar Sesión</Card.Title>
        <Card.Img variant="top" src="./logo.png" alt="Logo" />
      </Card.Header>
      <Card.Body>
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3" controlId="username">
            <Form.Label>Nombre de Usuario</Form.Label>
            <Form.Control
              type="text"
              placeholder="@nickname"
              value={UserAccount.username}
              onChange={(e) =>
                setUserAccount({ ...UserAccount, username: e.target.value })
              }
              required
            />
          </Form.Group>
          <Form.Group className="mb-3" controlId="password">
            <Form.Label>Contraseña</Form.Label>
            <Form.Control
              type="password"
              placeholder="Ingresa tu contraseña"
              value={UserAccount.password}
              onChange={(e) =>
                setUserAccount({ ...UserAccount, password: e.target.value })
              }
              required
            />
          </Form.Group>

          <div className="d-flex justify-content-between ">
            <Button variant="primary" type="submit">
              Iniciar Sesión
            </Button>
            <RegisterModal />
          </div>
        </Form>
      </Card.Body>
    </Card>
  );
};
