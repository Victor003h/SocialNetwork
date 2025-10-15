// src/components/Login/LoginForm.tsx
import React, { useState } from "react";
import { Form, Button, Card } from "react-bootstrap";

interface LoginFormProps {
  onLogin: (username: string) => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onLogin }) => {
  const [username, setUsername] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) onLogin(username);
  };

  return (
    <Card className="p-4 shadow-sm">
      <Card.Body>
        <h4 className="text-center mb-4">Iniciar sesión</h4>
        <Form onSubmit={handleSubmit}>
          <Form.Group className="mb-3" controlId="username">
            <Form.Label>Nombre de usuario</Form.Label>
            <Form.Control
              type="text"
              placeholder="Ingresa tu nombre"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </Form.Group>
          <div className="d-grid">
            <Button variant="primary" type="submit">
              Entrar
            </Button>
          </div>
        </Form>
      </Card.Body>
    </Card>
  );
};
