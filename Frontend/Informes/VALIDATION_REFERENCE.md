# Guía Rápida de Validación de Formularios

## 📁 Estructura de Archivos

```
Frontend/src/
├── components/
│   └── DistributedLogin/
│       ├── DistributedLogin.tsx          ← Componente principal con lógica
│       ├── LoginHeader.tsx
│       ├── BannerImage.tsx
│       ├── WelcomeSection.tsx
│       ├── LoginMethodToggle.tsx
│       ├── InputField.tsx               ← Con soporte a errores
│       ├── SeedPhraseField.tsx          ← Con contador de palabras
│       ├── ConnectButton.tsx
│       ├── SecurityInfo.tsx
│       ├── Footer.tsx
│       ├── ValidationAlert.tsx          ← NUEVO: Alerta de errores
│       ├── ToastMessage.tsx             ← NUEVO: Notificaciones
│       └── index.ts
└── utils/
    ├── validators.ts                     ← NUEVO: Lógica de validación
    └── validators.test.ts                ← NUEVO: Ejemplos de prueba
```

## 🔧 Funciones Disponibles

### En `src/utils/validators.ts`

```typescript
// Validadores individuales
isValidUrl(url: string): boolean
isSecureUrl(url: string): boolean
isValidSeedPhrase(seedPhrase: string): boolean
isSeedPhraseFormatValid(seedPhrase: string): boolean

// Validación completa
validateLoginForm(
  serverUrl: string,
  seedPhrase: string
): ValidationResult

// Utilidades
getFieldError(
  errors: ValidationError[],
  fieldName: string
): string | undefined
```

## 📊 Tipos de Datos

```typescript
interface ValidationError {
  field: string; // "serverUrl" | "seedPhrase"
  message: string; // Mensaje de error
}

interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

type ToastType = "success" | "error" | "warning" | "info";
```

## 🎯 Casos de Uso Comunes

### 1. Validar URL antes de enviar

```typescript
const validation = validateLoginForm(serverUrl, seedPhrase);
if (!validation.isValid) {
  // Mostrar errores
  setValidationErrors(validation.errors);
}
```

### 2. Obtener error de un campo específico

```typescript
const urlError = getFieldError(errors, "serverUrl");
if (urlError) {
  console.log(urlError); // "URL must use HTTPS protocol for security"
}
```

### 3. Mostrar notificación de éxito

```typescript
setToast({
  message: "Login successful!",
  type: "success",
  duration: 3000,
});
```

## ✅ Reglas de Validación

### URL del Servidor

- ✔ Requerido (no puede estar vacío)
- ✔ Debe ser una URL válida
- ✔ Debe usar HTTPS (protocolo seguro)
- ✔ Ejemplo: `https://node-primary.mesh.net`

### Seed Phrase

- ✔ Requerido (no puede estar vacío)
- ✔ Debe tener exactamente 12 o 24 palabras
- ✔ Solo puede contener letras (a-z, A-Z)
- ✔ Las palabras se separan por espacios
- ✔ Ejemplo: `abandon abandon abandon ... (12 o 24 palabras)`

## 🎨 Componentes Validación UI

### ValidationAlert

```tsx
<ValidationAlert
  errors={validationErrors}
  onDismiss={() => setValidationErrors([])}
/>
```

- Muestra todos los errores en una alerta Bootstrap
- Icono de error, título y lista de mensajes
- Botón para cerrar

### ToastMessage

```tsx
<ToastMessage message="Conexión exitosa!" type="success" duration={5000} />
```

- Notificación flotante en esquina inferior derecha
- Auto-cierre después de duración especificada
- Tipos: success, error, warning, info

### InputField mejorado

```tsx
<InputField
  label="Server URL"
  icon="dns"
  value={url}
  onChange={setUrl}
  error={getFieldError(errors, "serverUrl")}
/>
```

- Clase `is-invalid` si hay error
- Muestra mensaje de error en rojo

### SeedPhraseField mejorado

```tsx
<SeedPhraseField
  label="Seed Phrase"
  value={phrase}
  onChange={setPhrase}
  error={getFieldError(errors, "seedPhrase")}
/>
```

- Contador de palabras dinámico
- Muestra mensaje de error en rojo
- Contador solo visible si hay texto y sin errores

## 🚀 Flujo de Uso Típico

```
1. Usuario escribe URL
   └─ Se limpian errores previos de ese campo

2. Usuario escribe Seed Phrase
   └─ Se limpian errores previos de ese campo
   └─ Se muestra contador de palabras

3. Usuario hace clic en "Connect"
   └─ Se valida el formulario completo
   └─ Si hay errores:
      ├─ Se muestran en ValidationAlert
      ├─ Se destaca campos en rojo
      └─ Se muestra Toast de error
   └─ Si es válido:
      ├─ Se envía la solicitud
      ├─ Se muestra spinner de carga
      └─ Se muestra Toast de éxito/error según resultado
```

## 🧪 Testing

Abrir navegador → Consola → Copiar contenido de `validators.test.ts`

```javascript
// Verificar validadores
console.log(isValidUrl("https://example.com")); // true
console.log(isSecureUrl("http://example.com")); // false

// Validar formulario completo
const result = validateLoginForm(
  "https://node.example.com",
  "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
);
console.log(result); // { isValid: true, errors: [] }
```

## 📚 Ejemplo Completo

```tsx
import { DistributedLogin } from "./components/DistributedLogin";

export default function App() {
  return <DistributedLogin />;
}
```

El componente `DistributedLogin` maneja:

- ✅ Estado del formulario
- ✅ Validación en tiempo real
- ✅ Mostrar/ocultar errores
- ✅ Notificaciones de usuario
- ✅ Manejo de carga y errores
