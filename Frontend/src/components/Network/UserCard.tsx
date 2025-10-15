// src/components/Network/UserCard.tsx
import React from "react";
import { Card, Button, Badge } from "react-bootstrap";
import { User } from "../../types/user";
import { getStatusLabel, getStatusVariant } from "../../utils/StatusHelper";

interface UserCardProps {
  user: User;
  onJoin: (userId: string) => void;
}

export const UserCard: React.FC<UserCardProps> = ({ user, onJoin }) => {
  const variant = getStatusVariant(user.isActive);

  return (
    <Card className="mb-3 shadow-sm">
      <Card.Body className="d-flex justify-content-between align-items-center">
        <div>
          <h6 className="mb-1">{user.name}</h6>
          <Badge bg={variant}>{getStatusLabel(user.isActive)}</Badge>
        </div>
        <Button
          variant="outline-primary"
          size="sm"
          onClick={() => onJoin(user.id)}
        >
          Unirse
        </Button>
      </Card.Body>
    </Card>
  );
};
