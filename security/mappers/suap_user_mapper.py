from domain.user import User

class SuapUserMapper:
    @staticmethod
    def to_domain(data: dict) -> User:
        return User(
            matricula=str(data.get("identificacao", "")),
            name=data.get("nome_social", "") or data.get("nome_usual"),
            email=data.get("email", ""),
            cpf=str(data.get("cpf", "")).replace(".", "").replace("-", ""),
            tipo_usuario=data.get("tipo_usuario"),
            campus=data.get("campus"),
            atleta=False
        )