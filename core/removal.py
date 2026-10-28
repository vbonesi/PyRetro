"""Remover jogo: deste PC, cópia do Drive (lixeira) ou os dois (etapa F do plano de 28/10).

Três ações distintas, sempre com prévia e confirmação:

* `local`: tira do PC os arquivos exclusivos do conjunto (lixeira do sistema, recuperável).
* `drive`: manda à lixeira do Drive as cópias do conjunto (recuperável por até 30 dias).
* `both`: as duas, com resultado individual de cada item.

Saves, estados, texturas, capa, cadastro, nota e tempo NUNCA são tocados. Um jogo iniciado e não
finalizado ou fixado fica protegido (`blocked`) até a proteção ser retirada. A aplicação refaz a
prévia e só age se o `token` ainda for o mesmo (o que foi confirmado é o que será feito).

Este módulo não fala com o Drive nem com a lixeira: recebe `drive_list`, `drive_trash` e `trash`
de quem chama, o que mantém as regras testáveis sem rede e sem apagar nada de verdade.
"""
import hashlib
import json

SCOPES = ('local', 'drive', 'both')


class Blocked(ValueError):
    """A ação não pode ser feita agora; a mensagem diz por quê e o que fazer."""


def _token(plan):
    keys = {k: plan[k] for k in ('scope', 'code', 'entry', 'local', 'drive')}
    return hashlib.sha256(json.dumps(keys, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:24]


def plan(scope, code, entry, *, local_plan, drive_list=None, protected=(), can_write_drive=False, running=False):
    """Prévia da remoção.

    `local_plan`: dict de `mobile_roms.removal_plan` (remove/preserve/complete) ou None se o jogo
    não está no PC. `drive_list`: lista de {'path','id','size'} das cópias no Drive (None = não
    consultado). `protected`: motivos que protegem o jogo (iniciado, fixado...)."""
    if scope not in SCOPES:
        raise ValueError('ação desconhecida: ' + str(scope))
    do_local, do_drive = scope in ('local', 'both'), scope in ('drive', 'both')
    blocked, warnings = [], []
    if running:
        blocked.append('o jogo está em execução ou transferindo; feche-o antes')
    blocked += [f'protegido: {reason}' for reason in protected]
    local_files = []
    if do_local:
        if not local_plan:
            warnings.append('o jogo não está neste PC; nada a remover localmente')
        else:
            if not local_plan.get('complete', True):
                blocked.append('não foi possível provar quais arquivos são exclusivos; nada será removido')
            local_files = list(local_plan.get('remove', []))
            if local_plan.get('preserve'):
                warnings.append(f"{len(local_plan['preserve'])} arquivo(s) usados por outro conjunto serão preservados")
    drive_files = []
    if do_drive:
        if not can_write_drive:
            blocked.append('o Drive está só para leitura neste PC; reconecte o rclone com permissão de escrita')
        elif drive_list is None:
            blocked.append('não foi possível consultar o Drive agora; tente de novo online')
        else:
            drive_files = sorted(({'path': f['path'], 'id': f.get('id', ''), 'size': int(f.get('size', 0))} for f in drive_list),
                                 key=lambda f: f['path'])
            if not drive_files:
                warnings.append('nenhuma cópia deste jogo no Drive')
    if scope == 'local' and local_files and drive_list is not None and not drive_list:
        warnings.append('esta é a última cópia conhecida do jogo (não há cópia no Drive)')
    if scope == 'drive' and drive_files and not local_plan:
        warnings.append('esta é a última cópia conhecida do jogo (não há cópia neste PC)')
    result = {'version': 1, 'scope': scope, 'code': code, 'entry': entry, 'local': sorted(local_files),
              'drive': drive_files, 'preserved': sorted((local_plan or {}).get('preserve', [])),
              'bytes_drive': sum(f['size'] for f in drive_files), 'blocked': blocked, 'warnings': warnings,
              'keeps': ['saves e estados', 'texturas', 'capa', 'cadastro, nota e tempo'], 'requires_confirmation': True}
    result['token'] = _token(result)
    result['confirm_text'] = confirm_text(result)
    return result


def apply(current, token, confirm, *, trash, drive_trash):
    """Executa uma prévia já refeita (`current`) se o `token` confirmado ainda vale e a confirmação
    é a frase exata `current['confirm_text']`. Cada item tem resultado próprio; um erro não
    interrompe os demais (lote remoto não é atômico)."""
    if current['blocked']:
        raise Blocked('; '.join(current['blocked']))
    if token != current['token']:
        raise Blocked('o conteúdo mudou desde a prévia; veja a prévia de novo antes de confirmar')
    if confirm != confirm_text(current):
        raise Blocked('confirmação diferente da exibida')
    results = []
    for path in current['local']:
        try:
            trash(path); results.append({'where': 'local', 'item': path, 'ok': True})
        except Exception as error:  # noqa: BLE001 - cada item reporta o seu erro
            results.append({'where': 'local', 'item': path, 'ok': False, 'error': str(error)})
    for item in current['drive']:
        try:
            drive_trash(item); results.append({'where': 'drive', 'item': item['path'], 'ok': True})
        except Exception as error:  # noqa: BLE001
            results.append({'where': 'drive', 'item': item['path'], 'ok': False, 'error': str(error)})
    return {'scope': current['scope'], 'results': results, 'ok': all(r['ok'] for r in results),
            'recover': 'Drive: lixeira por até 30 dias; PC: lixeira do sistema.'}


def confirm_text(plan_):
    """Frase que o usuário confirma, com local e Drive por extenso (sem caixa persistente)."""
    parts = []
    if plan_['local']:
        parts.append(f"{len(plan_['local'])} arquivo(s) deste PC")
    if plan_['drive']:
        parts.append(f"{len(plan_['drive'])} arquivo(s) do Drive")
    return 'Mandar para a lixeira: ' + (' e '.join(parts) or 'nada') + f" ({plan_['entry']})"
