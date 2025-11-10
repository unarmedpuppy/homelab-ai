/**
 * Trade Entry Form Component
 * 
 * Comprehensive form for entering trades of all types:
 * - STOCK
 * - OPTION (with options chain inputs)
 * - CRYPTO_SPOT
 * - CRYPTO_PERP
 * - PREDICTION_MARKET
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  TextField,
  MenuItem,
  Grid,
  Typography,
  Paper,
  Divider,
  Chip,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
} from '@mui/material'
import { format } from 'date-fns'
import { TradeType, TradeSide, TradeStatus, OptionType, TradeCreate } from '../../types/trade'
import { useCreateTrade } from '../../hooks/useTrades'
import OptionsChainInput from './OptionsChainInput'

export default function TradeEntryForm() {
  const navigate = useNavigate()
  const createTrade = useCreateTrade()

  // Form state
  const [ticker, setTicker] = useState('')
  const [tradeType, setTradeType] = useState<TradeType>('STOCK')
  const [side, setSide] = useState<TradeSide>('LONG')
  const [status, setStatus] = useState<TradeStatus>('open')

  // Entry details
  const [entryPrice, setEntryPrice] = useState('')
  const [entryQuantity, setEntryQuantity] = useState('')
  const [entryTime, setEntryTime] = useState(format(new Date(), "yyyy-MM-dd'T'HH:mm"))
  const [entryCommission, setEntryCommission] = useState('0')

  // Exit details
  const [hasExit, setHasExit] = useState(false)
  const [exitPrice, setExitPrice] = useState('')
  const [exitQuantity, setExitQuantity] = useState('')
  const [exitTime, setExitTime] = useState('')
  const [exitCommission, setExitCommission] = useState('0')

  // Options fields
  const [strikePrice, setStrikePrice] = useState('')
  const [expirationDate, setExpirationDate] = useState('')
  const [optionType, setOptionType] = useState<OptionType | ''>('')
  const [delta, setDelta] = useState('')
  const [gamma, setGamma] = useState('')
  const [theta, setTheta] = useState('')
  const [vega, setVega] = useState('')
  const [rho, setRho] = useState('')
  const [impliedVolatility, setImpliedVolatility] = useState('')
  const [volume, setVolume] = useState('')
  const [openInterest, setOpenInterest] = useState('')
  const [bidPrice, setBidPrice] = useState('')
  const [askPrice, setAskPrice] = useState('')
  const [bidAskSpread, setBidAskSpread] = useState('')

  // Crypto fields
  const [cryptoExchange, setCryptoExchange] = useState('')
  const [cryptoPair, setCryptoPair] = useState('')

  // Prediction market fields
  const [predictionMarketPlatform, setPredictionMarketPlatform] = useState('')
  const [predictionOutcome, setPredictionOutcome] = useState('')

  // Risk management
  const [stopLoss, setStopLoss] = useState('')
  const [takeProfit, setTakeProfit] = useState('')

  // Metadata
  const [playbook, setPlaybook] = useState('')
  const [notes, setNotes] = useState('')
  const [tags, setTags] = useState('')

  // Validation
  const [errors, setErrors] = useState<Record<string, string>>({})

  // Handle field changes
  const handleFieldChange = (field: string, value: string) => {
    switch (field) {
      case 'strikePrice':
        setStrikePrice(value)
        break
      case 'expirationDate':
        setExpirationDate(value)
        break
      case 'optionType':
        setOptionType(value as OptionType)
        break
      case 'delta':
        setDelta(value)
        break
      case 'gamma':
        setGamma(value)
        break
      case 'theta':
        setTheta(value)
        break
      case 'vega':
        setVega(value)
        break
      case 'rho':
        setRho(value)
        break
      case 'impliedVolatility':
        setImpliedVolatility(value)
        break
      case 'volume':
        setVolume(value)
        break
      case 'openInterest':
        setOpenInterest(value)
        break
      case 'bidPrice':
        setBidPrice(value)
        break
      case 'askPrice':
        setAskPrice(value)
        break
      case 'bidAskSpread':
        setBidAskSpread(value)
        break
    }
  }

  // Validate form
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!ticker.trim()) {
      newErrors.ticker = 'Ticker is required'
    }

    if (!entryPrice || parseFloat(entryPrice) <= 0) {
      newErrors.entryPrice = 'Entry price must be greater than 0'
    }

    if (!entryQuantity || parseFloat(entryQuantity) <= 0) {
      newErrors.entryQuantity = 'Entry quantity must be greater than 0'
    }

    if (!entryTime) {
      newErrors.entryTime = 'Entry time is required'
    }

    if (hasExit) {
      if (!exitPrice || parseFloat(exitPrice) <= 0) {
        newErrors.exitPrice = 'Exit price must be greater than 0'
      }
      if (!exitQuantity || parseFloat(exitQuantity) <= 0) {
        newErrors.exitQuantity = 'Exit quantity must be greater than 0'
      }
      if (!exitTime) {
        newErrors.exitTime = 'Exit time is required'
      }
      if (exitTime && entryTime && new Date(exitTime) < new Date(entryTime)) {
        newErrors.exitTime = 'Exit time must be after entry time'
      }
    }

    if (tradeType === 'OPTION') {
      if (!strikePrice || parseFloat(strikePrice) <= 0) {
        newErrors.strikePrice = 'Strike price is required for options'
      }
      if (!expirationDate) {
        newErrors.expirationDate = 'Expiration date is required for options'
      }
      if (!optionType) {
        newErrors.optionType = 'Option type is required'
      }
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validate()) {
      return
    }

    // Build trade object
    const trade: TradeCreate = {
      ticker: ticker.toUpperCase().trim(),
      trade_type: tradeType,
      side,
      entry_price: parseFloat(entryPrice),
      entry_quantity: parseFloat(entryQuantity),
      entry_time: entryTime,
      entry_commission: parseFloat(entryCommission) || 0,
      exit_price: hasExit && exitPrice ? parseFloat(exitPrice) : undefined,
      exit_quantity: hasExit && exitQuantity ? parseFloat(exitQuantity) : undefined,
      exit_time: hasExit && exitTime ? exitTime : undefined,
      exit_commission: parseFloat(exitCommission) || 0,
      status: hasExit ? 'closed' : status,
      playbook: playbook || undefined,
      notes: notes || undefined,
      tags: tags
        ? tags
            .split(',')
            .map((t) => t.trim())
            .filter((t) => t.length > 0)
        : undefined,
      // Note: stop_loss and take_profit are not stored in the database
      // They are only used for R-multiple calculation parameter, not persisted
    }

    // Add options fields if trade type is OPTION
    if (tradeType === 'OPTION') {
      trade.strike_price = strikePrice ? parseFloat(strikePrice) : undefined
      trade.expiration_date = expirationDate || undefined
      trade.option_type = optionType || undefined
      trade.delta = delta ? parseFloat(delta) : undefined
      trade.gamma = gamma ? parseFloat(gamma) : undefined
      trade.theta = theta ? parseFloat(theta) : undefined
      trade.vega = vega ? parseFloat(vega) : undefined
      trade.rho = rho ? parseFloat(rho) : undefined
      trade.implied_volatility = impliedVolatility ? parseFloat(impliedVolatility) : undefined
      trade.volume = volume ? parseInt(volume) : undefined
      trade.open_interest = openInterest ? parseInt(openInterest) : undefined
      trade.bid_price = bidPrice ? parseFloat(bidPrice) : undefined
      trade.ask_price = askPrice ? parseFloat(askPrice) : undefined
      trade.bid_ask_spread = bidAskSpread ? parseFloat(bidAskSpread) : undefined
    }

    // Add crypto fields if trade type is crypto
    if (tradeType === 'CRYPTO_SPOT' || tradeType === 'CRYPTO_PERP') {
      trade.crypto_exchange = cryptoExchange || undefined
      trade.crypto_pair = cryptoPair || undefined
    }

    // Add prediction market fields if trade type is prediction market
    if (tradeType === 'PREDICTION_MARKET') {
      trade.prediction_market_platform = predictionMarketPlatform || undefined
      trade.prediction_outcome = predictionOutcome || undefined
    }

    try {
      await createTrade.mutateAsync(trade)
      navigate('/')
    } catch (error) {
      console.error('Error creating trade:', error)
    }
  }

  // Reset options fields when trade type changes
  useEffect(() => {
    if (tradeType !== 'OPTION') {
      setStrikePrice('')
      setExpirationDate('')
      setOptionType('')
      setDelta('')
      setGamma('')
      setTheta('')
      setVega('')
      setRho('')
      setImpliedVolatility('')
      setVolume('')
      setOpenInterest('')
      setBidPrice('')
      setAskPrice('')
      setBidAskSpread('')
    }
  }, [tradeType])

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Trade Entry
      </Typography>

      {createTrade.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {(() => {
            const error = createTrade.error
            if (!error) return 'Error creating trade. Please check your inputs and try again.'
            
            // Check if it's an Axios error with response data
            if ('response' in error && error.response) {
              const data = error.response.data
              if (data && typeof data === 'object' && 'detail' in data) {
                const detail = data.detail
                if (typeof detail === 'string') {
                  return detail
                }
                return JSON.stringify(detail)
              }
            }
            
            // Check if it's a standard Error
            if (error instanceof Error) {
              return error.message
            }
            
            return 'Error creating trade. Please check your inputs and try again.'
          })()}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          {/* Basic Information */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              required
              label="Ticker Symbol"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              error={!!errors.ticker}
              helperText={errors.ticker}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              required
              select
              label="Trade Type"
              value={tradeType}
              onChange={(e) => setTradeType(e.target.value as TradeType)}
            >
              <MenuItem value="STOCK">Stock</MenuItem>
              <MenuItem value="OPTION">Option</MenuItem>
              <MenuItem value="CRYPTO_SPOT">Crypto Spot</MenuItem>
              <MenuItem value="CRYPTO_PERP">Crypto Perpetual</MenuItem>
              <MenuItem value="PREDICTION_MARKET">Prediction Market</MenuItem>
            </TextField>
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              required
              select
              label="Side"
              value={side}
              onChange={(e) => setSide(e.target.value as TradeSide)}
            >
              <MenuItem value="LONG">Long</MenuItem>
              <MenuItem value="SHORT">Short</MenuItem>
            </TextField>
          </Grid>

          {/* Entry Details */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Entry Details
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              required
              label="Entry Price"
              type="number"
              value={entryPrice}
              onChange={(e) => setEntryPrice(e.target.value)}
              error={!!errors.entryPrice}
              helperText={errors.entryPrice}
              inputProps={{ step: '0.01', min: '0' }}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              required
              label="Entry Quantity"
              type="number"
              value={entryQuantity}
              onChange={(e) => setEntryQuantity(e.target.value)}
              error={!!errors.entryQuantity}
              helperText={errors.entryQuantity}
              inputProps={{ step: '0.01', min: '0' }}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              required
              label="Entry Time"
              type="datetime-local"
              value={entryTime}
              onChange={(e) => setEntryTime(e.target.value)}
              error={!!errors.entryTime}
              helperText={errors.entryTime}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>

          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              label="Entry Commission"
              type="number"
              value={entryCommission}
              onChange={(e) => setEntryCommission(e.target.value)}
              inputProps={{ step: '0.01', min: '0' }}
            />
          </Grid>

          {/* Exit Details */}
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={hasExit}
                  onChange={(e) => setHasExit(e.target.checked)}
                />
              }
              label="Trade is closed (has exit)"
            />
          </Grid>

          {hasExit && (
            <>
              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  required
                  label="Exit Price"
                  type="number"
                  value={exitPrice}
                  onChange={(e) => setExitPrice(e.target.value)}
                  error={!!errors.exitPrice}
                  helperText={errors.exitPrice}
                  inputProps={{ step: '0.01', min: '0' }}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  required
                  label="Exit Quantity"
                  type="number"
                  value={exitQuantity}
                  onChange={(e) => setExitQuantity(e.target.value)}
                  error={!!errors.exitQuantity}
                  helperText={errors.exitQuantity}
                  inputProps={{ step: '0.01', min: '0' }}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  required
                  label="Exit Time"
                  type="datetime-local"
                  value={exitTime}
                  onChange={(e) => setExitTime(e.target.value)}
                  error={!!errors.exitTime}
                  helperText={errors.exitTime}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12} sm={6} md={4}>
                <TextField
                  fullWidth
                  label="Exit Commission"
                  type="number"
                  value={exitCommission}
                  onChange={(e) => setExitCommission(e.target.value)}
                  inputProps={{ step: '0.01', min: '0' }}
                />
              </Grid>
            </>
          )}

          {/* Options Chain Input */}
          {tradeType === 'OPTION' && (
            <Grid item xs={12}>
              <OptionsChainInput
                strikePrice={strikePrice}
                expirationDate={expirationDate}
                optionType={optionType}
                delta={delta}
                gamma={gamma}
                theta={theta}
                vega={vega}
                rho={rho}
                impliedVolatility={impliedVolatility}
                volume={volume}
                openInterest={openInterest}
                bidPrice={bidPrice}
                askPrice={askPrice}
                bidAskSpread={bidAskSpread}
                onChange={handleFieldChange}
              />
            </Grid>
          )}

          {/* Crypto Fields */}
          {(tradeType === 'CRYPTO_SPOT' || tradeType === 'CRYPTO_PERP') && (
            <>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Crypto Information
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Exchange"
                  value={cryptoExchange}
                  onChange={(e) => setCryptoExchange(e.target.value)}
                  placeholder="e.g., Binance, Coinbase"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Trading Pair"
                  value={cryptoPair}
                  onChange={(e) => setCryptoPair(e.target.value)}
                  placeholder="e.g., BTC/USDT, ETH/USD"
                />
              </Grid>
            </>
          )}

          {/* Prediction Market Fields */}
          {tradeType === 'PREDICTION_MARKET' && (
            <>
              <Grid item xs={12}>
                <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                  Prediction Market Information
                </Typography>
                <Divider sx={{ mb: 2 }} />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Platform"
                  value={predictionMarketPlatform}
                  onChange={(e) => setPredictionMarketPlatform(e.target.value)}
                  placeholder="e.g., Polymarket, Kalshi"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Outcome"
                  value={predictionOutcome}
                  onChange={(e) => setPredictionOutcome(e.target.value)}
                  placeholder="e.g., YES, NO"
                />
              </Grid>
            </>
          )}

          {/* Risk Management */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Risk Management
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Stop Loss"
              type="number"
              value={stopLoss}
              onChange={(e) => setStopLoss(e.target.value)}
              inputProps={{ step: '0.01', min: '0' }}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Take Profit"
              type="number"
              value={takeProfit}
              onChange={(e) => setTakeProfit(e.target.value)}
              inputProps={{ step: '0.01', min: '0' }}
            />
          </Grid>

          {/* Metadata */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
              Metadata
            </Typography>
            <Divider sx={{ mb: 2 }} />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Playbook/Strategy"
              value={playbook}
              onChange={(e) => setPlaybook(e.target.value)}
              placeholder="e.g., Breakout, Reversal"
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <TextField
              fullWidth
              label="Tags (comma-separated)"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g., momentum, tech, earnings"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Additional notes about this trade..."
            />
          </Grid>

          {/* Submit Button */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 2 }}>
              <Button
                variant="outlined"
                onClick={() => navigate('/')}
                disabled={createTrade.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={createTrade.isPending}
                startIcon={createTrade.isPending ? <CircularProgress size={20} /> : null}
              >
                {createTrade.isPending ? 'Creating...' : 'Create Trade'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Paper>
  )
}

