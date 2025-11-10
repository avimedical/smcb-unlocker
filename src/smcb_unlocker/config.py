from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(yaml_file=['config.yaml'])

    base_url: str
    mgmt_username: str
    mgmt_password: str
    smcb_pin: str
