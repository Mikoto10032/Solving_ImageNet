import torch
import torch.nn as nn
from timm import create_model
from timm.models.tresnet_v2 import InplacABN_to_ABN
from timm.utils.kd.helpers import fuse_bn2d_bn1d_abn
import torchvision.transforms as T


class build_kd_model(nn.Module):
    def __init__(self, args=None):
        super(build_kd_model, self).__init__()

        model_kd = create_model(
            model_name=args.kd_model_name,
            checkpoint_path=args.kd_model_path,
            pretrained=False,
            num_classes=args.num_classes,
            in_chans=3)

        model_kd.cpu().eval()
        model_kd = InplacABN_to_ABN(model_kd)
        model_kd = fuse_bn2d_bn1d_abn(model_kd)
        self.model = model_kd.cuda().eval()
        self.mean_model_kd = self.model.default_cfg['mean']
        self.std_model_kd = self.model.default_cfg['std']

    def normalize_input(self, input, model):
        mean_student = model.default_cfg['mean']
        std_student = model.default_cfg['std']

        input_kd = input
        if mean_student != self.mean_model_kd or std_student != self.std_model_kd:
            std = (self.std_model_kd[0] / std_student[0], self.std_model_kd[1] / std_student[1],
                   self.std_model_kd[2] / std_student[2])
            transform_std = T.Normalize(mean=(0, 0, 0), std=std)

            mean = (self.mean_model_kd[0] - mean_student[0], self.mean_model_kd[1] - mean_student[1],
                    self.mean_model_kd[2] - mean_student[2])
            transform_mean = T.Normalize(mean=mean, std=(1, 1, 1))

            input_kd = transform_mean(transform_std(input))

        return input_kd
