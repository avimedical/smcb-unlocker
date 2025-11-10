from dataclasses import dataclass, replace


@dataclass
class StateContext:
    smcb_key: str
    smcb_pin: str
    session_id: str | None = None

    def with_smcb_key(self, smcb_key: str) -> StateContext:
        return replace(self, smcb_key=smcb_key)
    
    def with_smcb_pin(self, smcb_pin: str) -> StateContext:
        return replace(self, smcb_pin=smcb_pin)

    def with_session_id(self, session_id: str) -> StateContext:
        return replace(self, session_id=session_id)
