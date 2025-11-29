import { useState } from "react";
import { Modal, Button, Form } from "react-bootstrap";
import HandleRegister from "./HandleRegister";

interface RegisterData {
  firstName: string;
  lastName: string;
  username: string;
  password: string;
  email: string;
  phone: string;
}

const RegisterModal = () => {
  const [show, setShow] = useState(false);

  const handleClose = () => setShow(false);
  const handleShow = () => setShow(true);

  const [formData, setFormData] = useState<RegisterData>({
    firstName: "",
    lastName: "",
    username: "",
    password: "",
    email: "",
    phone: "",
  });

  const handleChange = (field: keyof RegisterData, value: string) => {
    setFormData({
      ...formData,
      [field]: value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    HandleRegister.registerUser(formData).then((response) => {
      if (response.ok) {
        alert("Usuario registrado correctamente.");
        handleClose();
      } else {
        alert(`Error: ${response.message}`);
      }
    });
  };

  return (
    <>
      {/* BOTÓN PARA ABRIR MODAL */}
      <Button variant="primary" onClick={handleShow}>
        Registrarse
      </Button>

      {/* MODAL */}
      <Modal show={show} onHide={handleClose} centered>
        <Modal.Header closeButton>
          <Modal.Title>Crear cuenta</Modal.Title>
        </Modal.Header>

        <Modal.Body>
          <Form onSubmit={handleSubmit}>
            <Form.Group className="mb-3">
              <Form.Label>First Name</Form.Label>
              <Form.Control
                type="text"
                value={formData.firstName}
                onChange={(e) => handleChange("firstName", e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Last Name</Form.Label>
              <Form.Control
                type="text"
                value={formData.lastName}
                onChange={(e) => handleChange("lastName", e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>@Username</Form.Label>
              <Form.Control
                type="text"
                value={formData.username}
                onChange={(e) => handleChange("username", e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Password</Form.Label>
              <Form.Control
                type="password"
                value={formData.password}
                onChange={(e) => handleChange("password", e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Email</Form.Label>
              <Form.Control
                type="email"
                value={formData.email}
                onChange={(e) => handleChange("email", e.target.value)}
                required
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label>Phone Number</Form.Label>
              <Form.Control
                type="tel"
                value={formData.phone}
                onChange={(e) => handleChange("phone", e.target.value)}
              />
            </Form.Group>

            <Button variant="success" type="submit">
              Registrar
            </Button>
          </Form>
        </Modal.Body>
      </Modal>
    </>
  );
};

export default RegisterModal;
