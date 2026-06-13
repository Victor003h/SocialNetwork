import React from "react";
import { User } from "../types/feed.types";

interface FriendsBubblesProps {
  friends: User[];
  onlineIds: number[];
  onSelect: (friend: User) => void;
}

const avatarFor = (user: User) =>
  user.avatarUrl ||
  `https://ui-avatars.com/api/?name=${user.username}&background=random`;

// Fila horizontal de seguidos con indicador de conexión (verde/gris).
const FriendsBubbles: React.FC<FriendsBubblesProps> = ({
  friends,
  onlineIds,
  onSelect,
}) => {
  const onlineSet = new Set(onlineIds);

  return (
    <section className="mb-4">
      <div className="d-flex justify-content-between align-items-center mb-2">
        <small className="text-muted fw-bold">SIGUIENDO</small>
      </div>
      <div
        className="d-flex gap-3 overflow-auto pb-2"
        style={{ scrollbarWidth: "none" }}
      >
        {friends.length === 0 && (
          <small className="text-muted">
            Aún no sigues a nadie. Ve a Search para seguir usuarios.
          </small>
        )}

        {friends.map((friend) => {
          const isOnline = onlineSet.has(friend.id);
          return (
            <div
              key={friend.id}
              className="text-center"
              style={{ cursor: "pointer" }}
              onClick={() => onSelect(friend)}
            >
              <div
                className="position-relative rounded-circle p-1 border border-primary mx-auto"
                style={{ width: 54, height: 54 }}
              >
                <img
                  src={avatarFor(friend)}
                  className="rounded-circle w-100 h-100"
                  alt={friend.username}
                />
                <span
                  className={`position-absolute rounded-circle border border-dark ${
                    isOnline ? "bg-success" : "bg-secondary"
                  }`}
                  title={isOnline ? "Conectado" : "Desconectado"}
                  style={{
                    width: 14,
                    height: 14,
                    bottom: 2,
                    right: 2,
                  }}
                ></span>
              </div>
              <small
                className="d-block mt-1 text-white"
                style={{ fontSize: "10px" }}
              >
                {friend.username}
              </small>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default FriendsBubbles;
