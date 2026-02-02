# Validación de Formularios - Login Distribuido

## 📋 Overview

Se ha implementado un sistema completo de validación de formularios en el login distribuido con Bootstrap. La validación es robusta, user-friendly e informativa.

## ✨ Características de Validación

### 1. **Validación de URL del Servidor**

- ✅ Verifica que la URL sea válida
- ✅ Exige protocolo HTTPS (seguridad)
- ✅ Mensajes de error específicos

```typescript
isValidUrl(url); // Valida formato de URL
isSecureUrl(url); // Verifica que use HTTPS
```

### 2. **Validación de Seed Phrase**

- ✅ Verifica cantidad de palabras (12 o 24)
- ✅ Valida que solo contenga palabras (sin números/caracteres especiales)
- ✅ Muestra contador dinámico de palabras
- ✅ Mensajes de error claros

```typescript
isValidSeedPhrase(seedPhrase); // Valida 12 o 24 palabras
isSeedPhraseFormatValid(phrase); // Valida caracteres válidos
```

### 3. **Validación Completa del Formulario**

```typescript
validateLoginForm(serverUrl, seedPhrase);
// Retorna:
// {
//   isValid: boolean,
//   errors: ValidationError[]
// }
```

## 🎨 Componentes de Validación

### **ValidationAlert**

Muestra alertas de error con:

- Icono de error
- Lista de errores
- Botón de cerrar
- Estilo Bootstrap alert-danger

```tsx
<ValidationAlert
  errors={validationErrors}
  onDismiss={() => setValidationErrors([])}
/>
```

### **ToastMessage**

Notificaciones flotantes en la esquina inferior derecha con:

- Tipos: success, error, warning, info
- Auto-cierre tras 5 segundos
- Icono dinámico según tipo
- Despido manual

```tsx
<ToastMessage
  message="Connection successful!"
  type="success"
  duration={5000}
  onClose={() => setToast(null)}
/>
```

### **InputField (Mejorado)**

- Muestra errores en rojo (clase `is-invalid`)
- Mensaje de error debajo del campo
- Limpia errores al escribir

```tsx
<InputField
  label="Server / Node URL"
  icon="dns"
  value={formData.serverUrl}
  onChange={handleChange}
  error={getFieldError(errors, "serverUrl")}
/>
```

### **SeedPhraseField (Mejorado)**

- Contador dinámico de palabras
- Muestra errores de validación
- Contador solo aparece cuando hay texto y sin errores
- Campo monoespaciado para mejor legibilidad

```tsx
<SeedPhraseField
  label="Private Key / Seed Phrase"
  value={formData.seedPhrase}
  onChange={handleChange}
  error={getFieldError(errors, "seedPhrase")}
  onQRScan={handleQRScan}
/>
```

## 🔄 Flujo de Validación

### **En tiempo real (On-change)**

1. Usuario escribe en un campo
2. Errores previos de ese campo se limpian automáticamente
3. Se mantienen errores de otros campos

### **Al enviar el formulario**

1. Se valida todo el formulario
2. Si hay errores:
   - Se muestran en `ValidationAlert`
   - Se destacan campos en rojo (is-invalid)
   - Se muestra Toast de error
   - Botón "Connect" se deshabilita
3. Si todo es válido:
   - Se envía la solicitud
   - Se muestra Toast de éxito
   - Loading spinner activo

## 📋 Mensajes de Error

### **Errores de URL**

- `"Server URL is required"`
- `"Please enter a valid URL (e.g., https://example.com)"`
- `"URL must use HTTPS protocol for security"`

### **Errores de Seed Phrase**

- `"Seed phrase is required"`
- `"Seed phrase contains invalid characters"`
- `"Seed phrase must contain 12 or 24 words (found X)"`

## 🎯 Ejemplo de Uso

```tsx
import { DistributedLogin } from "./components/DistributedLogin";

export default function App() {
  return <DistributedLogin />;
}
```

## 🧪 Pruebas de Validación

### **Caso 1: URL inválida**

```
Input: "example.com"
Error: "URL must use HTTPS protocol for security"
```

### **Caso 2: Seed phrase con números**

```
Input: "word1 word2 word3 ... (12 palabras con número)"
Error: "Seed phrase contains invalid characters"
```

### **Caso 3: Seed phrase con 11 palabras**

```
Input: "word word word ... (11 palabras)"
Error: "Seed phrase must contain 12 or 24 words (found 11)"
```

### **Caso 4: Todo válido**

```
Input:
  URL: "https://node-primary.mesh.net"
  Phrase: "abandon abandon abandon ... (12 o 24 palabras válidas)"
Status: ✅ Validación exitosa
```

## 🔐 Consideraciones de Seguridad

1. **HTTPS Obligatorio**: Las URLs deben usar protocolo seguro
2. **No se almacenan credenciales**: Las validaciones son locales
3. **Seed phrase no se transmite**: Se valida pero no se guarda
4. **Mensajes informativos**: Ayudan sin revelar información sensible

## 🚀 Próximas Mejoras

- [ ] Validación de palabras contra diccionario BIP39
- [ ] Sugerencias de autocompletado para palabras
- [ ] Rate limiting en intentos de conexión
- [ ] Almacenamiento seguro con localStorage (encrypted)
- [ ] Recuperación de contraseña
- [ ] Autenticación de dos factores (2FA)
