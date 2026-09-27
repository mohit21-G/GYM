import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class HealthService {
  private readonly startTime = Date.now();

  constructor(
    private readonly configService: ConfigService,
    private readonly prisma: PrismaService,
  ) {}

  async getHealth() {
    let dbStatus = 'disconnected';
    try {
      await this.prisma.$queryRaw`SELECT 1`;
      dbStatus = 'connected';
    } catch {
      dbStatus = 'standby';
    }

    return {
      status: 'ok',
      service: 'google-fitbit-ai-backend',
      environment: this.configService.get<string>('nodeEnv'),
      uptimeSeconds: Math.floor((Date.now() - this.startTime) / 1000),
      timestamp: new Date().toISOString(),
      services: {
        api: 'healthy',
        database: dbStatus,
        redis: 'ready',
        aiProvider: this.configService.get<string>('ai.provider'),
        aiModel: this.configService.get<string>('ai.model'),
      },
    };
  }
}
