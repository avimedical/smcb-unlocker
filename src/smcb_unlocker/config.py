from pydantic import BaseModel
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource


class ConfigKonnektor(BaseModel):
    base_url: str
    interval: int


class ConfigUserCredentials(BaseModel):
    username: str
    password: str


class ConfigPinCredentials(BaseModel):
    pin: str


class ConfigCredentials(BaseModel):
    konnektors: dict[str, ConfigUserCredentials]
    kt: dict[str, ConfigUserCredentials]
    smcb: dict[str, ConfigPinCredentials]


class Config(BaseSettings):
    model_config = SettingsConfigDict(yaml_file=['config.yaml'])

    konnektors: dict[str, ConfigKonnektor]
    credentials: ConfigCredentials

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (YamlConfigSettingsSource(settings_cls),)
