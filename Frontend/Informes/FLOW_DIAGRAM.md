# 📊 Diagrama de Flujo - Sistema de Validación

## 🔄 Flujo Principal

```
┌─────────────────────────────────────────────────────────┐
│              INICIO: Página de Login                    │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────▼────────────────┐
        │   DistributedLogin.tsx       │
        │  - Estado del formulario     │
        │  - Errores de validación    │
        │  - Toast notification       │
        └─────────────┬────────────────┘
                      │
        ┌─────────────▼────────────────┐
        │   Renderizar Componentes     │
        │  - LoginHeader               │
        │  - BannerImage               │
        │  - WelcomeSection            │
        │  - InputFields               │
        │  - ConnectButton             │
        │  - ValidationAlert           │
        │  - ToastMessage              │
        └─────────────┬────────────────┘
                      │
        ┌─────────────▼────────────────────────────────┐
        │      Usuario Escribe en Campo               │
        │  onChange → handleInputChange()              │
        └─────────────┬────────────────────────────────┘
                      │
        ┌─────────────▼───────────────────────────────┐
        │  Limpiar Error del Campo                   │
        │  setValidationErrors(prev =>                │
        │    prev.filter(e => e.field !== field))    │
        └─────────────┬───────────────────────────────┘
                      │
    ┌─────────────────▼──────────────────────┐
    │  ¿Hay más contenido?                   │
    ├─────────────────┬──────────────────────┤
    │ SÍ: Mostrar     │ NO: Ocultar contador │
    │ Contador palabras│                      │
    └─────────────────┴──────────────────────┘
                      │
        ┌─────────────▼────────────────┐
        │  Usuario Hace Clic "Connect" │
        └─────────────┬────────────────┘
                      │
        ┌─────────────▼─────────────────────────────┐
        │  handleConnect()                          │
        │  1. Validar formulario                   │
        │  2. validateLoginForm(url, phrase)       │
        └─────────────┬─────────────────────────────┘
                      │
        ┌─────────────▼─────────────────────────────┐
        │  ¿Validación Exitosa?                    │
        └─────────────┬──────────────────┬──────────┘
                      │ NO               │ SÍ
        ┌─────────────▼──────┐  ┌────────▼──────────┐
        │  MOSTRAR ERRORES   │  │  ENVIAR SOLICITUD │
        └────┬────────────┬──┘  └────────┬──────────┘
             │            │              │
     ┌───────▼┐  ┌────────▼───────┐    │
     │Mostrar │  │Mostrar Toast   │    │
     │ValidationAlert  │ de ERROR   │    │
     │(alert-danger)   │ (alert-danger)  │
     └───────┬──────────┴────────┬──────┘
             │                   │
     ┌───────▼──────────┐        │
     │Destacar campos   │        │
     │en ROJO           │        │
     │(is-invalid)      │        │
     └───────┬──────────┘        │
             │                   │
     ┌───────▼──────────┐        │
     │Deshabilitar      │        │
     │botón Connect     │        │
     └──────────────────┘        │
                                 │
                    ┌────────────▼────────────┐
                    │  setIsLoading(true)     │
                    │  Mostrar Spinner        │
                    │  Enviar Datos al Backend│
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  ¿Respuesta del Server? │
                    └─────┬──────────────┬────┘
                          │ Éxito        │ Error
                    ┌─────▼──┐   ┌──────▼──────┐
                    │Mostrar │   │Mostrar Toast│
                    │Toast   │   │ de ERROR    │
                    │SUCCESS │   │(alert-danger)
                    └─────┬──┘   └──────┬──────┘
                          │           │
                    ┌─────▼───────────▼──────┐
                    │  setIsLoading(false)   │
                    │  Usuario puede reintentar
                    └────────────┬───────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  ¿Redireccionar?       │
                    │  (setTimeout 2000ms)   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Ir a Dashboard        │
                    │  o siguiente paso      │
                    └────────────────────────┘
```

## 📝 Detalles del Flujo

### 1. Carga Inicial

```
DistributedLogin monta
    ↓
Estado inicial:
  - loginMethod: "node"
  - serverUrl: ""
  - seedPhrase: ""
  - validationErrors: []
  - toast: null
    ↓
Renderiza componentes
```

### 2. En tiempo real (Mientras escribe)

```
Usuario escribe
    ↓
onChange dispara handleInputChange
    ↓
setFormData con nuevo valor
    ↓
setValidationErrors limpia error del campo
    ↓
SeedPhraseField calcula contador de palabras
    ↓
Re-render del componente
```

### 3. Al hacer clic en "Connect"

```
onClick dispara handleConnect
    ↓
validateLoginForm verifica:
  ├─ URL no vacía
  ├─ URL formato válido
  ├─ URL usa HTTPS
  ├─ Seed phrase no vacía
  ├─ Seed phrase tiene 12 o 24 palabras
  └─ Seed phrase solo tiene letras
    ↓
¿Hay errores?
├─ SÍ:
│  ├─ setValidationErrors(errors)
│  ├─ setToast({type: "error"})
│  └─ return (no enviar)
│
└─ NO:
   ├─ setIsLoading(true)
   ├─ setValidationErrors([])
   ├─ Esperar 2 segundos (simulación)
   └─ setToast({type: "success"})
       ↓
   Opcional: redirigir después
```

## 🔍 Flujo de Validación Detallado

### Validación de URL

```
URL ingresada
    ↓
¿Está vacía?
├─ SÍ: Error "Server URL is required"
│
└─ NO:
   ├─ ¿Formato válido (URL)?
   │  ├─ NO: Error "Please enter a valid URL"
   │  │
   │  └─ SÍ:
   │     ├─ ¿Usa HTTPS?
   │     │  ├─ NO: Error "URL must use HTTPS protocol"
   │     │  │
   │     │  └─ SÍ: ✅ VÁLIDO
```

### Validación de Seed Phrase

```
Seed phrase ingresada
    ↓
¿Está vacía?
├─ SÍ: Error "Seed phrase is required"
│
└─ NO:
   ├─ ¿Solo contiene letras?
   │  ├─ NO: Error "contains invalid characters"
   │  │
   │  └─ SÍ:
   │     ├─ ¿Tiene 12 o 24 palabras?
   │     │  ├─ NO: Error "must contain 12 or 24 words (found X)"
   │     │  │
   │     │  └─ SÍ: ✅ VÁLIDO
```

## 🎯 Estados del Componente

```
Estado INITIAL
├─ Campos: vacíos
├─ Botón: deshabilitado
├─ Errores: []
└─ Toast: null

Estado EDITING
├─ Usuario escribe
├─ Errores pueden aparecer
├─ Botón: habilitado si válido
└─ Toast: null

Estado VALIDATING
├─ Hace clic Connect
├─ Se valida el formulario
├─ Errores se muestran si existen
└─ Toast: error si validación falla

Estado LOADING
├─ Enviando solicitud
├─ Campos: deshabilitados
├─ Botón: spinner activo
├─ Errores: ocultos
└─ Toast: "Connecting..."

Estado SUCCESS
├─ Solicitud exitosa
├─ Toast: "Connection successful!"
└─ Redirigir después de 2s

Estado ERROR
├─ Solicitud falló
├─ Toast: "Connection failed"
└─ Usuario puede reintentar
```

## 🔐 Flujo de Seguridad

```
Validación en Cliente
    ├─ Formato URL
    ├─ Protocolo HTTPS
    ├─ Cantidad de palabras
    └─ Caracteres válidos
         ↓
    Si todo es válido
         ↓
    Enviar HTTPS al servidor
         ↓
    Validación en Servidor (IMPORTANTE)
         ├─ Verificar URL contra lista blanca
         ├─ Validar seed phrase contra BIP39
         ├─ Verificar con blockchain
         └─ Crear sesión segura
              ↓
         Responder al cliente
              ├─ Éxito: Token/Cookie
              └─ Error: Mensaje seguro
```

## 📱 Flujo Responsive

```
Todos los tamaños de pantalla
    ├─ Mobile (< 576px)
    │  └─ Mismo layout, ancho 100%
    ├─ Tablet (576px - 991px)
    │  └─ Ancho máximo 448px, centrado
    └─ Desktop (≥ 992px)
       └─ Ancho máximo 448px, centrado
```

## 🧪 Flujo de Testing

```
1. Validadores
   ├─ isValidUrl()
   ├─ isSecureUrl()
   ├─ isValidSeedPhrase()
   └─ isSeedPhraseFormatValid()

2. Componentes
   ├─ ValidationAlert (mostrar/ocultar)
   ├─ ToastMessage (aparece/desaparece)
   ├─ InputField (error/no error)
   └─ SeedPhraseField (contador actualiza)

3. Flujo completo
   ├─ Usuario escribe
   ├─ Se valida
   ├─ Se muestran errores
   ├─ Usuario corrige
   ├─ Se envía
   └─ Se muestra resultado
```

## ⚡ Optimizaciones

```
Render:
├─ Validación solo se ejecuta al hacer clic
├─ Errores se limpian solo del campo escrito
├─ Toast se auto-cierra después de tiempo
└─ Re-render minimizado con memo()

Estado:
├─ Estado local en componente
├─ No es necesario Context/Redux
├─ Fácil de extender si es necesario
└─ Escalable para múltiples formularios
```
