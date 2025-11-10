/**
 * Options Chain Input Component
 * 
 * Displays options-specific fields (Greeks, strike, expiration, etc.)
 * Only shown when trade_type is OPTION.
 */

import {
  Grid,
  TextField,
  MenuItem,
  Typography,
  Divider,
  Box,
} from '@mui/material'
import { OptionType } from '../../types/trade'

interface OptionsChainInputProps {
  strikePrice: string
  expirationDate: string
  optionType: OptionType | ''
  delta: string
  gamma: string
  theta: string
  vega: string
  rho: string
  impliedVolatility: string
  volume: string
  openInterest: string
  bidPrice: string
  askPrice: string
  bidAskSpread: string
  onChange: (field: string, value: string) => void
}

export default function OptionsChainInput({
  strikePrice,
  expirationDate,
  optionType,
  delta,
  gamma,
  theta,
  vega,
  rho,
  impliedVolatility,
  volume,
  openInterest,
  bidPrice,
  askPrice,
  bidAskSpread,
  onChange,
}: OptionsChainInputProps) {
  return (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
        Options Chain Information
      </Typography>
      <Divider sx={{ mb: 2 }} />

      <Grid container spacing={2}>
        {/* Strike Price */}
        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Strike Price"
            type="number"
            value={strikePrice}
            onChange={(e) => onChange('strikePrice', e.target.value)}
            inputProps={{ step: '0.01', min: '0' }}
          />
        </Grid>

        {/* Expiration Date */}
        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Expiration Date"
            type="date"
            value={expirationDate}
            onChange={(e) => onChange('expirationDate', e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
        </Grid>

        {/* Option Type */}
        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            select
            label="Option Type"
            value={optionType}
            onChange={(e) => onChange('optionType', e.target.value)}
          >
            <MenuItem value="CALL">CALL</MenuItem>
            <MenuItem value="PUT">PUT</MenuItem>
          </TextField>
        </Grid>

        {/* Greeks Section */}
        <Grid item xs={12}>
          <Typography variant="subtitle1" sx={{ mt: 1, mb: 1 }}>
            Greeks
          </Typography>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Delta"
            type="number"
            value={delta}
            onChange={(e) => onChange('delta', e.target.value)}
            inputProps={{ step: '0.0001', min: '-1', max: '1' }}
            helperText="Price sensitivity"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Gamma"
            type="number"
            value={gamma}
            onChange={(e) => onChange('gamma', e.target.value)}
            inputProps={{ step: '0.0001', min: '0' }}
            helperText="Delta sensitivity"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Theta"
            type="number"
            value={theta}
            onChange={(e) => onChange('theta', e.target.value)}
            inputProps={{ step: '0.0001' }}
            helperText="Time decay (per day)"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Vega"
            type="number"
            value={vega}
            onChange={(e) => onChange('vega', e.target.value)}
            inputProps={{ step: '0.0001', min: '0' }}
            helperText="Volatility sensitivity"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Rho"
            type="number"
            value={rho}
            onChange={(e) => onChange('rho', e.target.value)}
            inputProps={{ step: '0.0001' }}
            helperText="Interest rate sensitivity"
          />
        </Grid>

        {/* Market Data Section */}
        <Grid item xs={12}>
          <Typography variant="subtitle1" sx={{ mt: 1, mb: 1 }}>
            Market Data
          </Typography>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Implied Volatility (IV)"
            type="number"
            value={impliedVolatility}
            onChange={(e) => onChange('impliedVolatility', e.target.value)}
            inputProps={{ step: '0.01', min: '0', max: '100' }}
            helperText="As percentage (e.g., 25 for 25%)"
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Volume"
            type="number"
            value={volume}
            onChange={(e) => onChange('volume', e.target.value)}
            inputProps={{ step: '1', min: '0' }}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Open Interest"
            type="number"
            value={openInterest}
            onChange={(e) => onChange('openInterest', e.target.value)}
            inputProps={{ step: '1', min: '0' }}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Bid Price"
            type="number"
            value={bidPrice}
            onChange={(e) => onChange('bidPrice', e.target.value)}
            inputProps={{ step: '0.01', min: '0' }}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Ask Price"
            type="number"
            value={askPrice}
            onChange={(e) => onChange('askPrice', e.target.value)}
            inputProps={{ step: '0.01', min: '0' }}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <TextField
            fullWidth
            label="Bid-Ask Spread"
            type="number"
            value={bidAskSpread}
            onChange={(e) => onChange('bidAskSpread', e.target.value)}
            inputProps={{ step: '0.01', min: '0' }}
            helperText="Difference between bid and ask"
          />
        </Grid>
      </Grid>
    </Box>
  )
}

