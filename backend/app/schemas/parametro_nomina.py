from pydantic import BaseModel, ConfigDict


class ParametroNominaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    anio_fiscal: int
    isr_tramo1_hasta: float
    isr_tramo2_hasta: float
    isr_tramo3_hasta: float
    isr_tramo2_tasa: float
    isr_tramo3_tasa: float
    isr_tramo4_tasa: float
    tss_sfs_empleado_pct: float
    tss_sfs_patronal_pct: float
    tss_afp_empleado_pct: float
    tss_afp_patronal_pct: float
    tss_riesgos_laborales_pct: float
    tss_infotep_pct: float
    tss_tope_sfs_salarios_minimos: int
    tss_tope_afp_salarios_minimos: int
    salario_minimo_referencia: float
    notas: str | None
