// src/components/Network/NetworkPage.tsx
import React, { useEffect, useState } from "react";
import { Container, Row, Col, Spinner } from "react-bootstrap";
import { User } from "../../types/user";
import { fetchUsers, joinNetwork } from "../../utils/api";
import { UserCard } from "./UserCard";

export const NetworkPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const data = await fetchUsers();
      setUsers(data);
      setLoading(false);
    };
    load();
  }, []);

  const handleJoin = async (userId: string) => {
    await joinNetwork(userId);
    alert(`Te has unido al usuario ${userId}`);
  };

  if (loading) return <Spinner animation="border" />;

  return (
    <Container className="mt-4">
      <h3 className="mb-4">Usuarios en la red</h3>
      <Row>
        <Col md={6}>
          {users.map((u) => (
            <UserCard key={u.id} user={u} onJoin={handleJoin} />
          ))}
        </Col>
      </Row>
    </Container>
  );
};
