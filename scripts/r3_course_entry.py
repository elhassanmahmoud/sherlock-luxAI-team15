"""Course entry point, copied to sherlock/main.py by build_r3_course_candidate."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

KIND = "sherlock_r3_selective_movement_0105658"
V14_SHA = "98a0735005926ecd47b52f9c290110069893e4a44c2304b063f1551ffd96d3d8"
R3_SHA = "99b07775582e68efef8b63f545980e969cb0ed3c7d65052b48179508b87dd7b9"


def check_payload(bundle):
    if bundle["kind"] != KIND:
        raise ValueError("Expected the registered R3 selective movement candidate")
    for key, expected in (("v14", V14_SHA), ("r3", R3_SHA)):
        if not isinstance(bundle[key], bytes) or sha256(bundle[key]).hexdigest() != expected:
            raise ValueError(f"Unexpected {key} checkpoint")


class Agent_x:
    def __init__(self, player, agent_path=None, name="Sherlock R3 Agent_X", train=False):
        self.player, self.name, self.env_cfg = player, name, None
        self.load_agent(agent_path or "agent.pth")

    def load_agent(self, load_path):
        import torch

        from .r3_adviser import SelectiveAdviceAgent

        path = Path(load_path)
        if not path.is_file():
            path = Path(__file__).resolve().parent / "weights" / path.name
        bundle = torch.load(path, map_location="cpu", weights_only=True)
        check_payload(bundle)
        with TemporaryDirectory(prefix="sherlock_r3_") as tmp:
            v14 = Path(tmp) / "v14.pth"
            v14.write_bytes(bundle["v14"])
            actor = SelectiveAdviceAgent(self.player, str(v14), name=self.name, train=False, seed=0,
                                         advice_path=BytesIO(bundle["r3"]), mode="movement")
        actor.cfg.frozen = True
        actor.set_to_eval_mode()
        if self.env_cfg is not None:
            actor.set_env_cfg(self.env_cfg)
        self.agent_path, self._actor = str(path.resolve()), actor

    def __getattr__(self, name):
        # Expose the original counters and config to the package check.
        return getattr(object.__getattribute__(self, "_actor"), name)

    def new_game(self, player=None):
        if player is not None:
            self.player = player
        self._actor.new_game(self.player)

    def set_env_cfg(self, env_cfg):
        self.env_cfg = env_cfg
        self._actor.set_env_cfg(env_cfg)

    def set_to_eval_mode(self):
        self._actor.set_to_eval_mode()

    def act(self, step, obs):
        return self._actor.act(step, obs)

    def update(self, step, obs, reward, action, terminated, next_obs):
        # The research game loop only observes through act; train=True must match that trajectory.
        return

    def save_agent(self, path=None):
        return


Agent = Agent_x
