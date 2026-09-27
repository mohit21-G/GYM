import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class HealthService {
  private readonly startTime = Date.now();

  constructor(private readonly configService: ConfigService) {}

  getHealth() {
    return {
      status: 'ok',
      service: 'google-fitbit-ai-backend',
      environment: this.configService.get<string>('nodeEnv'),
      uptimeSeconds: Math.floor((Date.now() - this.startTime) / 1000),
      timestamp: new Date().toISOString(),
      services: {
        api: 'healthy',
        database: 'configured',
        redis: 'ready',
        aiProvider: this.configService.get<string>('ai.provider'),
        aiModel: this.configService.get<string>('ai.model'),
      },
    };
  }
}
