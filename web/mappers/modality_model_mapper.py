from domain.modality import Modality
from web.models.response.modality_create_response import ModalityCreateResponse


class ModalityModelMapper:
    def to_create_response(self, modality: Modality) -> ModalityCreateResponse:
        return ModalityCreateResponse(
            modality_id=modality.id,
            name=modality.name,
            min_members=modality.min_members,
            max_members=modality.max_members,
            active=modality.active,
            message="Modalidade cadastrada com sucesso!",
        )
