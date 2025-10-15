// src/utils/statusHelpers.ts
export const getStatusVariant = (isActive: boolean): string =>
  isActive ? "success" : "danger";

export const getStatusLabel = (isActive: boolean): string =>
  isActive ? "Activo" : "Inactivo";
