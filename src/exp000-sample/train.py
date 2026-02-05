import hydra
import wandb
from omegaconf import DictConfig, OmegaConf


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig) -> None:
    # Initialize wandb
    wandb.init(
        project=cfg.wandb.project,
        entity=cfg.wandb.entity,
        name=cfg.exp_name,
        config=OmegaConf.to_container(cfg, resolve=True),
        mode=cfg.wandb.mode,
    )

    print(f"Experiment: {cfg.exp_name}")
    print(f"Config:\n{OmegaConf.to_yaml(cfg)}")

    # TODO: Implement training loop
    # 1. Load data
    # 2. Create model
    # 3. Train
    # 4. Evaluate
    # 5. Save model

    # Example logging
    for epoch in range(cfg.training.epochs):
        # Simulate training
        train_loss = 1.0 / (epoch + 1)
        val_loss = 1.1 / (epoch + 1)

        wandb.log({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
        })

        print(f"Epoch {epoch}: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")

    wandb.finish()


if __name__ == "__main__":
    main()
