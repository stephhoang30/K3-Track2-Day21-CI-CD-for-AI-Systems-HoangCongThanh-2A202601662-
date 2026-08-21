#!/usr/bin/env bash
#
# Dung phan ha tang mang + may ao cho lab Buoc 2.
#
#   bash scripts/setup_ec2.sh
#
# Da lam san truoc do (khong nam trong script nay):
#   - S3 bucket mlops-lab-244669245042, da chan public access
#   - IAM user  mlops-lab-ci          (doc + ghi bucket tren)
#   - IAM role  mlops-lab-ec2-role    (chi doc bucket tren)
#   - Instance profile mlops-lab-ec2-profile
#
# Script idempotent: chay lai nhieu lan khong tao trung tai nguyen.

set -euo pipefail

export AWS_PROFILE="${AWS_PROFILE:-mlops-lab}"
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}"

VPC_ID=vpc-0bc8343692ba5ca7f
SG_NAME=mlops-serve-sg
KEY_NAME=mlops-deploy
KEY_FILE="$HOME/.ssh/mlops_deploy"
INSTANCE_NAME=mlops-serve

say() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }

# -----------------------------------------------------------------------------
say "1/4 Security group $SG_NAME"
SG_ID=$(aws ec2 describe-security-groups \
          --filters "Name=group-name,Values=$SG_NAME" "Name=vpc-id,Values=$VPC_ID" \
          --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo None)

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
  SG_ID=$(aws ec2 create-security-group \
            --group-name "$SG_NAME" \
            --description "MLOps lab inference server" \
            --vpc-id "$VPC_ID" \
            --query GroupId --output text)
  echo "    da tao $SG_ID"
else
  echo "    da ton tai $SG_ID"
fi

# Port 22 de GitHub Actions SSH vao deploy, port 8000 cho inference API.
# Lab yeu cau endpoint public nen mo 0.0.0.0/0. Sau khi cham diem xong nen
# thu hep lai, hoac terminate instance han.
for PORT in 22 8000; do
  aws ec2 authorize-security-group-ingress \
    --group-id "$SG_ID" --protocol tcp --port "$PORT" --cidr 0.0.0.0/0 \
    >/dev/null 2>&1 && echo "    mo cong $PORT" || echo "    cong $PORT da mo tu truoc"
done

# -----------------------------------------------------------------------------
say "2/4 SSH key pair $KEY_NAME"
if [ -f "$KEY_FILE" ]; then
  echo "    $KEY_FILE da co, dung lai"
else
  ssh-keygen -t ed25519 -f "$KEY_FILE" -N "" -C "github-actions-deploy" >/dev/null
  echo "    da tao $KEY_FILE"
fi

if aws ec2 describe-key-pairs --key-names "$KEY_NAME" >/dev/null 2>&1; then
  echo "    key pair da co tren AWS"
else
  aws ec2 import-key-pair --key-name "$KEY_NAME" \
    --public-key-material "fileb://$KEY_FILE.pub" >/dev/null
  echo "    da import public key len AWS"
fi

# -----------------------------------------------------------------------------
say "3/4 EC2 instance $INSTANCE_NAME"
IID=$(aws ec2 describe-instances \
        --filters "Name=tag:Name,Values=$INSTANCE_NAME" \
                  "Name=instance-state-name,Values=pending,running" \
        --query 'Reservations[0].Instances[0].InstanceId' --output text 2>/dev/null || echo None)

if [ "$IID" = "None" ] || [ -z "$IID" ]; then
  AMI=$(aws ssm get-parameter \
          --name /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id \
          --query 'Parameter.Value' --output text)
  echo "    AMI Ubuntu 22.04: $AMI"

  IID=$(aws ec2 run-instances \
          --image-id "$AMI" \
          --instance-type t3.micro \
          --key-name "$KEY_NAME" \
          --security-group-ids "$SG_ID" \
          --iam-instance-profile "Name=mlops-lab-ec2-profile" \
          --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
          --query 'Instances[0].InstanceId' --output text)
  echo "    dang khoi dong $IID, cho instance running..."
  aws ec2 wait instance-running --instance-ids "$IID"
else
  echo "    da chay san: $IID"
fi

# -----------------------------------------------------------------------------
say "4/4 Ket qua"
VM_IP=$(aws ec2 describe-instances --instance-ids "$IID" \
          --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

cat <<SUMMARY

  Security group   $SG_ID
  Instance         $IID
  Public IP        $VM_IP
  SSH              ssh -i $KEY_FILE ubuntu@$VM_IP

Xong. Bao lai cho Claude kem dia chi IP o tren de chay tiep:
dvc push, nap GitHub Secrets, cau hinh VM va chay pipeline.

SUMMARY
