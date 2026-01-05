# Schema Primitive Types

YASL provides a rich set of primitive types to ensure your data is validated correctly. These include standard Python types, Pydantic's robust validation types, and even physical quantities with units.

## Standard Types

The foundational types you use every day.

*   `str` or `string`: Standard text.
*   `int`: Integer numbers.
*   `float`: Floating-point numbers.
*   `bool`: Boolean values (`true`/`false`).
*   `date`: ISO 8601 dates (e.g., `2023-12-31`).
*   `datetime`: ISO 8601 date-times (e.g., `2023-12-31T23:59:59`).
*   `clocktime`: Time of day (e.g., `14:30:00`). Note: Renamed from `time` to avoid conflict with physical time units.
*   `path`: Filesystem paths.
*   `url`: Standard URLs.
*   `any`: Accepts any value.
*   `map[<KeyType>, <ValueType>]`: Dictionary of key-value pairs (e.g., `map[str, int]`).
*   `ref[<target>]`: Reference to another unique property. See [Using References](references.md).
*   `type`: Validates that the value is a valid YASL type signature (e.g., `int`, `str`, `map[str, int]`, or a registered type `MyType`).
*   `markdown`: Validates that the value is valid Markdown text.

## Pydantic Types

YASL supports the full suite of Pydantic's specialized types for stricter validation.

### Numbers
*   `PositiveInt`, `NegativeInt`
*   `NonPositiveInt`, `NonNegativeInt`
*   `StrictInt`, `StrictFloat`, `StrictBool`
*   `PositiveFloat`, `NegativeFloat`
*   `FiniteFloat`

### Identifiers & Encoding
*   `UUID1`, `UUID3`, `UUID4`, `UUID5`, `UUID6`, `UUID7`, `UUID8`
*   `Base64Bytes`, `Base64Str`
*   `Base64UrlBytes`, `Base64UrlStr`

### Networking & Web
*   `EmailStr`, `NameEmail`
*   `IPvAnyAddress`
*   `AnyUrl`, `HttpUrl`, `FileUrl`, `FtpUrl`
*   `AnyWebsocketUrl`, `WebsocketUrl`

### Database DSNs
*   `PostgresDsn`, `MySQLDsn`, `MariaDBDsn`
*   `MongoDsn`, `RedisDsn`
*   `KafkaDsn`, `AmqpDsn`, `NatsDsn`
*   `ClickHouseDsn`, `CockroachDsn`, `SnowflakeDsn`

### Filesystem
*   `FilePath`: Validates that the file exists.
*   `DirectoryPath`: Validates that the directory exists.

## Physical Quantities (SI Units)

YASL allows you to define fields that require physical units (e.g., meters, seconds, kilograms). These types validate that the input string contains both a number and a compatible unit.

**Example:**
```yaml
properties:
  distance:
    type: length  # Accepts "10 m", "5 km", "100 ft"
  weight:
    type: mass    # Accepts "50 kg", "100 lbs"
```

### Supported Physical Types

*   **Space & Geometry**: `length`, `area`, `volume`, `angle`, `solid angle`, `wavenumber`, `plate scale`
*   **Time & Motion**: `time`, `frequency`, `speed`, `velocity`, `acceleration`, `angular speed`, `angular velocity`, `angular frequency`, `angular acceleration`, `jerk`, `jolt`, `snap`, `jounce`, `crackle`, `pop`, `pounce`, `absement`, `absity`, `frequency drift`
*   **Mechanics**: `mass`, `force`, `pressure`, `stress`, `mass density`, `specific volume`, `momentum`, `impulse`, `angular momentum`, `action`, `moment of inertia`, `surface tension`, `yank`, `surface mass density`, `linear density`, `compressibility`
*   **Energy & Power**: `energy`, `work`, `torque`, `power`, `radiant flux`, `energy density`, `specific energy`, `energy flux`, `irradiance`, `power density`
*   **Thermal**: `temperature`, `temperature gradient`, `heat capacity`, `entropy`, `specific heat capacity`, `specific entropy`, `thermal conductivity`, `thermal conductance`, `thermal resistance`, `thermal resistivity`, `molar heat capacity`
*   **Electromagnetism**: `electrical charge`, `electrical current`, `electrical potential`, `electrical resistance`, `electrical impedance`, `electrical reactance`, `electrical resistivity`, `electrical conductance`, `electrical conductivity`, `electrical capacitance`, `electrical dipole moment`, `electrical current density`, `electrical field strength`, `electrical flux density`, `surface charge density`, `polarization density`, `electrical charge density`, `permittivity`, `electrical mobility`, `magnetic flux`, `magnetic helicity`, `magnetic flux density`, `magnetic field strength`, `magnetic moment`, `electromagnetic field strength`, `permeability`, `inductance`, `magnetic reluctance`, `electron density`, `electron flux`, `electrical charge (ESU)`, `electrical current (ESU)`, `electrical current (EMU)`, `electrical charge (EMU)`
*   **Photometry & Radiometry**: `luminous intensity`, `luminous flux`, `luminous emittance`, `illuminance`, `luminance`, `luminous efficacy`, `radiant intensity`, `spectral flux density`, `surface brightness`, `spectral flux density wav`, `surface brightness wav`, `photon flux density`, `photon flux density wav`, `photon surface brightness`, `photon surface brightness wav`, `photon flux`, `radiance`, `opacity`, `mass attenuation coefficient`
*   **Chemistry & Materials**: `amount of substance`, `molar concentration`, `molar volume`, `reaction rate`, `catalytic activity`, `molality`, `chemical potential`, `molar conductivity`, `dynamic viscosity`, `diffusivity`, `kinematic viscosity`, `volumetric rate`, `volumetric flow rate`, `mass flux`, `momentum density`, `number density`, `particle flux`, `dose of ionizing radiation`
*   **Data**: `data quantity`, `bandwidth`
*   **Other**: `dimensionless`
