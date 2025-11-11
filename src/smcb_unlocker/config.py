from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, YamlConfigSettingsSource

class Config(BaseSettings):
    model_config = SettingsConfigDict(yaml_file=['config.yaml'])

    konnektor_base_url: str
    konnektor_admin_username: str
    konnektor_admin_password: str
    kt_base_url: str
    kt_mgmt_username: str
    kt_mgmt_password: str
    smcb_iccsn: str
    smcb_pin: str

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
